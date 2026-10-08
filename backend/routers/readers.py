"""读者档案与借书卡管理（管理员 / 图书员）"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import get_password_hash, require_librarian
from database import get_db
from models import Book, BorrowRecord, Category, FineRecord, Review, User
from schemas import UserCreate, UserResponse, UserUpdate
from services.audit import get_rules, record_audit
from services.circulation import enrich_borrow_record

router = APIRouter(prefix="/api/readers", tags=["读者档案"])


@router.get("", response_model=List[UserResponse], summary="读者检索")
def list_readers(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    query = db.query(User)
    if role_filter:
        query = query.filter(User.role == role_filter)
    if status_filter:
        query = query.filter(User.status == status_filter)
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                User.username.like(s),
                User.full_name.like(s),
                User.card_number.like(s),
                User.email.like(s),
                User.phone.like(s),
            )
        )
    return query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="录入新读者")
def create_reader_by_admin(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="电子邮箱已存在")

    card_number = user_in.card_number or f"CARD-{datetime.now().strftime('%Y%m')}{db.query(User).count() + 101:03d}"
    if db.query(User).filter(User.card_number == card_number).first():
        raise HTTPException(status_code=400, detail="借书卡号已存在")

    role = user_in.role or "reader"
    if role not in {"reader", "librarian", "admin"}:
        raise HTTPException(status_code=400, detail="用户角色无效")
    if role in ["admin", "librarian"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅系统管理员有权指派管理员或图书员角色")
    if user_in.status and user_in.status not in {"active", "frozen"}:
        raise HTTPException(status_code=400, detail="账户状态无效")
    if user_in.max_borrow_limit is not None and user_in.max_borrow_limit < 1:
        raise HTTPException(status_code=400, detail="最大借阅册数必须大于 0")
    if user_in.balance is not None and user_in.balance < 0:
        raise HTTPException(status_code=400, detail="账户余额不能为负数")

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        phone=user_in.phone,
        hashed_password=get_password_hash(user_in.password),
        role=role,
        card_number=card_number,
        max_borrow_limit=user_in.max_borrow_limit or 5,
        balance=user_in.balance or Decimal("0.00"),
        status=user_in.status or "active",
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="用户名、邮箱或借书卡号已存在")
    db.refresh(new_user)
    record_audit(db, current_user, "CREATE_READER", "USER", str(new_user.id),
                 f"录入新读者: {new_user.username} ({new_user.card_number})", request)
    return new_user


@router.put("/{reader_id}", response_model=UserResponse, summary="编辑读者信息")
def update_reader(
    reader_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    reader = db.query(User).filter(User.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="读者不存在")

    if current_user.role != "admin" and reader.role != "reader":
        raise HTTPException(status_code=403, detail="图书员仅可维护普通读者账户")

    if user_in.role and user_in.role not in {"reader", "librarian", "admin"}:
        raise HTTPException(status_code=400, detail="用户角色无效")
    if user_in.status and user_in.status not in {"active", "frozen"}:
        raise HTTPException(status_code=400, detail="账户状态无效")

    if user_in.role and user_in.role != reader.role:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="仅系统管理员有权修改用户角色")
        if reader.id == current_user.id:
            raise HTTPException(status_code=400, detail="不能修改当前管理员自己的管理员角色")
        reader.role = user_in.role

    if user_in.email is not None and user_in.email != reader.email:
        if db.query(User).filter(User.email == user_in.email, User.id != reader.id).first():
            raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
        reader.email = user_in.email
    if user_in.full_name:
        reader.full_name = user_in.full_name
    if user_in.phone is not None:
        reader.phone = user_in.phone
    if user_in.status:
        reader.status = user_in.status
    if user_in.max_borrow_limit is not None:
        if user_in.max_borrow_limit < 1:
            raise HTTPException(status_code=400, detail="最大借阅册数必须大于 0")
        reader.max_borrow_limit = user_in.max_borrow_limit
    if user_in.balance is not None:
        if user_in.balance < 0:
            raise HTTPException(status_code=400, detail="账户余额不能为负数")
        reader.balance = user_in.balance
    if user_in.password:
        reader.hashed_password = get_password_hash(user_in.password)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="用户信息已被其他账户占用")
    db.refresh(reader)
    record_audit(db, current_user, "UPDATE_READER", "USER", str(reader.id), f"更新用户资料: {reader.username}", request)
    return reader


@router.post("/{reader_id}/reset-password", summary="重置读者密码")
def reset_reader_password(
    reader_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    reader = db.query(User).filter(User.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="读者不存在")
    if current_user.role != "admin" and reader.role != "reader":
        raise HTTPException(status_code=403, detail="图书员仅可重置普通读者密码")

    reader.hashed_password = get_password_hash("123456")
    db.commit()
    record_audit(db, current_user, "RESET_PWD", "USER", str(reader.id), f"重置读者 {reader.username} 密码为默认 123456")
    return {"message": f"读者 {reader.username} 的密码已成功重置为 123456"}


@router.get("/{reader_id}/overview", summary="读者画像（借阅偏好/欠费/在借明细）")
def reader_overview(
    reader_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    reader = db.query(User).filter(User.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="读者不存在")

    total_borrows = db.query(BorrowRecord).filter(BorrowRecord.user_id == reader_id).count()
    active = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == reader_id, BorrowRecord.return_date.is_(None)
    ).all()

    rate = get_rules(db)["fine_rate"]
    enriched = [enrich_borrow_record(r, rate) for r in active]

    unpaid = db.query(func.sum(FineRecord.amount)).filter(
        FineRecord.user_id == reader_id, FineRecord.status == "unpaid"
    ).scalar() or Decimal("0.00")

    fav_rows = (
        db.query(Category.name, func.count(BorrowRecord.id).label("cnt"))
        .join(Book, Book.category_id == Category.id)
        .join(BorrowRecord, BorrowRecord.book_id == Book.id)
        .filter(BorrowRecord.user_id == reader_id)
        .group_by(Category.id)
        .order_by(desc("cnt"))
        .limit(5)
        .all()
    )

    return {
        "user": UserResponse.model_validate(reader),
        "total_borrows": total_borrows,
        "active_borrows": len(active),
        "overdue_borrows": len([r for r in enriched if r.status == "overdue"]),
        "unpaid_fines": unpaid,
        "review_count": db.query(Review).filter(Review.user_id == reader_id).count(),
        "favorite_categories": [{"name": name, "count": cnt} for name, cnt in fav_rows],
        "current_borrows": [
            {
                "record_id": r.id,
                "book_id": r.book_id,
                "title": r.book.title if r.book else "",
                "due_date": r.due_date,
                "status": r.status,
                "overdue_days": r.overdue_days,
                "calculated_fine": r.calculated_fine,
            }
            for r in enriched
        ],
    }
