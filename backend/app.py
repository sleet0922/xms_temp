import os
import csv
import io
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc

from database import get_db, init_db
from models import (
    User, Book, BookCopy, BorrowRecord, Reservation,
    FineRecord, Category, ShelfLocation, Announcement,
    AuditLog, SystemSetting
)
from schemas import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, TokenResponse, ChangePasswordRequest,
    BookCreate, BookUpdate, BookResponse, BookCopyCreate, BookCopyResponse,
    BorrowRecordCreate, QuickCirculationBorrow, QuickCirculationReturn, BorrowRecordResponse,
    ReservationCreate, ReservationResponse, FinePayRequest, FineRecordResponse,
    CategoryCreate, CategoryResponse, ShelfLocationCreate, ShelfLocationResponse,
    AnnouncementCreate, AnnouncementResponse, AuditLogResponse, SettingUpdate, SettingResponse,
    StatsOverview
)
from auth import (
    get_current_user, require_admin, require_librarian,
    create_access_token, get_password_hash, verify_password
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("library-api")

app = FastAPI(
    title="未来智慧图书馆管理系统 API (完全体)",
    version="2.0.0",
    description="支持 RBAC 权限隔离、全流程智慧借还台、条码追踪、逾期罚金及数据可视化的企业级图书管理系统"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    try:
        init_db()
        logger.info("数据库连接与数据模型初始化完成")
    except Exception as e:
        logger.warning(f"启动自动初始化跳过: {e}")

def record_audit(db: Session, user: Optional[User], action: str, target_type: str, target_id: str, detail: str, request: Optional[Request] = None):
    try:
        ip = request.client.host if request and request.client else "127.0.0.1"
        log = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else "anonymous",
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            detail=detail,
            ip_address=ip
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"审计日志写入失败: {e}")

def get_setting_val(db: Session, key: str, default: str) -> str:
    s = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
    return s.setting_value if s else default

def enrich_borrow_record(rec: BorrowRecord, daily_fine_rate: Decimal) -> BorrowRecord:
    now = datetime.now()
    if rec.status in ["borrowed", "overdue"] and not rec.return_date and now > rec.due_date:
        rec.status = "overdue"
        overdue_days = (now - rec.due_date).days
        rec.overdue_days = max(1, overdue_days)
        rec.calculated_fine = Decimal(str(rec.overdue_days)) * daily_fine_rate
    else:
        rec.overdue_days = 0
        rec.calculated_fine = Decimal("0.00")
    return rec

# ==========================================
# 1. 认证与个人中心
# ==========================================

@app.post("/api/auth/login", response_model=TokenResponse)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status == "frozen":
        raise HTTPException(status_code=403, detail="账户已被冻结，请联系服务台处理")

    token = create_access_token(data={"sub": user.username, "role": user.role})
    record_audit(db, user, "LOGIN", "USER", str(user.id), f"用户 {user.username} 成功登录系统", request)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="电子邮箱已被注册")

    # 自动生成读者借阅证卡号
    card_number = user_data.card_number
    if not card_number:
        card_number = f"CARD-{datetime.now().strftime('%Y%m')}{db.query(User).count() + 101:03d}"

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
        role="reader",
        card_number=card_number,
        max_borrow_limit=user_data.max_borrow_limit or 5,
        balance=Decimal("0.00"),
        status="active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    record_audit(db, new_user, "REGISTER", "USER", str(new_user.id), f"读者注册: {new_user.username}", request)
    return new_user

@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@app.put("/api/auth/profile", response_model=UserResponse)
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.email and user_update.email != current_user.email:
        if db.query(User).filter(User.email == user_update.email, User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail="该邮箱已被其他读者使用")
        current_user.email = user_update.email

    db.commit()
    db.refresh(current_user)
    return current_user

@app.put("/api/auth/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码不正确")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")

    current_user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    record_audit(db, current_user, "CHANGE_PASSWORD", "USER", str(current_user.id), "用户自主修改密码")
    return {"message": "密码修改成功，请妥善保管"}

# ==========================================
# 2. 统计报表与流通指标引擎
# ==========================================

@app.get("/api/stats/overview", response_model=StatsOverview)
def get_stats_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_books = db.query(Book).count()
    total_copies = db.query(BookCopy).count()
    total_readers = db.query(User).filter(User.role == "reader").count()
    active_borrows = db.query(BorrowRecord).filter(BorrowRecord.return_date.is_(None)).count()
    
    # 逾期计算
    overdue_borrows = db.query(BorrowRecord).filter(
        BorrowRecord.return_date.is_(None),
        BorrowRecord.due_date < datetime.now()
    ).count()

    today_borrows = db.query(BorrowRecord).filter(BorrowRecord.borrow_date >= today_start).count()
    today_returns = db.query(BorrowRecord).filter(BorrowRecord.return_date >= today_start).count()

    unpaid_fines_sum = db.query(func.sum(FineRecord.amount)).filter(FineRecord.status == "unpaid").scalar() or Decimal("0.00")

    user_borrowed = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.return_date.is_(None)
    ).count()

    user_overdue = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.return_date.is_(None),
        BorrowRecord.due_date < datetime.now()
    ).count()

    user_fines = db.query(func.sum(FineRecord.amount)).filter(
        FineRecord.user_id == current_user.id,
        FineRecord.status == "unpaid"
    ).scalar() or Decimal("0.00")

    return {
        "total_books": total_books,
        "total_copies": total_copies,
        "total_readers": total_readers,
        "active_borrows": active_borrows,
        "overdue_borrows": overdue_borrows,
        "today_borrows": today_borrows,
        "today_returns": today_returns,
        "unpaid_fines": unpaid_fines_sum,
        "user_borrowed": user_borrowed,
        "user_overdue": user_overdue,
        "user_fines": user_fines
    }

@app.get("/api/stats/trends")
def get_stats_trends(days: int = 15, db: Session = Depends(get_db)):
    """返回近 N 天的借还走势数据供前端绘制曲线"""
    timeline = []
    now = datetime.now()
    for i in range(days - 1, -1, -1):
        day_date = (now - timedelta(days=i)).date()
        day_start = datetime.combine(day_date, datetime.min.time())
        day_end = datetime.combine(day_date, datetime.max.time())
        
        borrow_cnt = db.query(BorrowRecord).filter(
            BorrowRecord.borrow_date >= day_start,
            BorrowRecord.borrow_date <= day_end
        ).count()

        return_cnt = db.query(BorrowRecord).filter(
            BorrowRecord.return_date >= day_start,
            BorrowRecord.return_date <= day_end
        ).count()

        timeline.append({
            "date": day_date.strftime("%m-%d"),
            "borrows": borrow_cnt,
            "returns": return_cnt
        })
    return timeline

@app.get("/api/stats/categories")
def get_category_stats(db: Session = Depends(get_db)):
    """返回各分类下的藏书与流通数量"""
    cats = db.query(Category).all()
    results = []
    for cat in cats:
        b_count = db.query(Book).filter(Book.category_id == cat.id).count()
        results.append({
            "id": cat.id,
            "name": cat.name,
            "code": cat.code,
            "count": b_count,
            "icon": cat.icon
        })
    return results

@app.get("/api/stats/popular-books")
def get_popular_books(limit: int = 8, db: Session = Depends(get_db)):
    """借阅热度最高图书"""
    books = db.query(Book).order_by(desc(Book.borrow_count)).limit(limit).all()
    return [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "isbn": b.isbn,
            "cover_url": b.cover_url,
            "borrow_count": b.borrow_count,
            "available_copies": b.available_copies
        }
        for b in books
    ]

# ==========================================
# 3. 分类与书架位置管理
# ==========================================

@app.get("/api/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).all()
    res = []
    for c in cats:
        cnt = db.query(Book).filter(Book.category_id == c.id).count()
        c_dict = {
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "description": c.description,
            "icon": c.icon,
            "created_at": c.created_at,
            "book_count": cnt
        }
        res.append(c_dict)
    return res

@app.post("/api/categories", response_model=CategoryResponse)
def create_category(cat: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(require_librarian)):
    if db.query(Category).filter(Category.code == cat.code).first():
        raise HTTPException(status_code=400, detail="分类编码已存在")
    new_cat = Category(**cat.dict())
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@app.get("/api/shelf-locations", response_model=List[ShelfLocationResponse])
def list_shelf_locations(db: Session = Depends(get_db)):
    return db.query(ShelfLocation).all()

@app.post("/api/shelf-locations", response_model=ShelfLocationResponse)
def create_shelf_location(loc: ShelfLocationCreate, db: Session = Depends(get_db), current_user: User = Depends(require_librarian)):
    if db.query(ShelfLocation).filter(ShelfLocation.code == loc.code).first():
        raise HTTPException(status_code=400, detail="书架位置编码已存在")
    new_loc = ShelfLocation(**loc.dict())
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc

# ==========================================
# 4. 图书书目与单册实体管理
# ==========================================

@app.get("/api/books", response_model=List[BookResponse])
def list_books(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    location_id: Optional[int] = None,
    in_stock_only: bool = False,
    sort_by: str = "created_at",
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Book)
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.like(s),
                Book.author.like(s),
                Book.isbn.like(s),
                Book.publisher.like(s),
                Book.tags.like(s)
            )
        )
    if category_id:
        query = query.filter(Book.category_id == category_id)
    if location_id:
        query = query.filter(Book.location_id == location_id)
    if in_stock_only:
        query = query.filter(Book.available_copies > 0)

    if sort_by == "borrow_count":
        query = query.order_by(desc(Book.borrow_count))
    elif sort_by == "price":
        query = query.order_by(desc(Book.price))
    else:
        query = query.order_by(desc(Book.created_at))

    return query.offset(skip).limit(limit).all()

@app.get("/api/books/{book_id}", response_model=BookResponse)
def get_book_detail(book_id: int, db: Session = Depends(get_db)):
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="图书不存在")
    return b

@app.post("/api/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    book_in: BookCreate,
    copies_count: int = Query(1, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None
):
    if db.query(Book).filter(Book.isbn == book_in.isbn).first():
        raise HTTPException(status_code=400, detail="该 ISBN 书目已在馆内登记，请直接添加单册")

    new_book = Book(
        **book_in.dict(),
        total_copies=copies_count,
        available_copies=copies_count,
        borrow_count=0
    )
    db.add(new_book)
    db.flush()

    # 自动生成单册条形码
    for i in range(1, copies_count + 1):
        barcode = f"BK-{datetime.now().strftime('%Y%m')}-{new_book.id:04d}-{i:02d}"
        copy = BookCopy(
            book_id=new_book.id,
            barcode=barcode,
            status="available",
            condition_status="good",
            location_note="新编目入库"
        )
        db.add(copy)

    db.commit()
    db.refresh(new_book)
    record_audit(db, current_user, "CREATE_BOOK", "BOOK", str(new_book.id), f"录入新书: {new_book.title} (副本数: {copies_count})", request)
    return new_book

@app.put("/api/books/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book_in: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian)
):
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="图书不存在")

    for k, v in book_in.dict(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    return b

@app.delete("/api/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    request: Request = None
):
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="图书不存在")

    # 检查是否有在借记录
    in_use = db.query(BorrowRecord).filter(BorrowRecord.book_id == book_id, BorrowRecord.return_date.is_(None)).first()
    if in_use:
        raise HTTPException(status_code=400, detail="该图书尚有读者借阅未归还，无法注销下架")

    title = b.title
    db.delete(b)
    db.commit()
    record_audit(db, current_user, "DELETE_BOOK", "BOOK", str(book_id), f"注销图书: {title}", request)
    return None

@app.post("/api/books/{book_id}/copies", response_model=BookCopyResponse)
def add_book_copy(
    book_id: int,
    copy_in: BookCopyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian)
):
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="图书不存在")
    if db.query(BookCopy).filter(BookCopy.barcode == copy_in.barcode).first():
        raise HTTPException(status_code=400, detail="条形码已存在")

    copy = BookCopy(
        book_id=book_id,
        barcode=copy_in.barcode,
        status="available",
        condition_status=copy_in.condition_status or "good",
        location_note=copy_in.location_note
    )
    b.total_copies += 1
    b.available_copies += 1
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy

@app.get("/api/books-export")
def export_books_csv(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "书名", "作者", "ISBN", "出版社", "出版日期", "定价", "总册数", "在馆册数", "借阅次数"])
    for b in books:
        writer.writerow([
            b.id, b.title, b.author, b.isbn, b.publisher or "", b.publish_date or "",
            f"{b.price:.2f}", b.total_copies, b.available_copies, b.borrow_count
        ])
    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=library_books.csv"}
    )

# ==========================================
# 5. 智慧借还流通服务台 (Circulation Desk)
# ==========================================

@app.post("/api/circulation/borrow", response_model=BorrowRecordResponse)
def quick_borrow(
    circ: QuickCirculationBorrow,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None
):
    """服务台快速扫码借书：借书卡号 + 单册条形码"""
    reader = db.query(User).filter(User.card_number == circ.card_number).first()
    if not reader:
        raise HTTPException(status_code=404, detail=f"未找到借书卡号为 {circ.card_number} 的读者")
    if reader.status == "frozen":
        raise HTTPException(status_code=403, detail="该读者借书卡已被冻结，无法借阅")

    # 检查未付罚金
    unpaid = db.query(FineRecord).filter(FineRecord.user_id == reader.id, FineRecord.status == "unpaid").count()
    if unpaid > 0:
        raise HTTPException(status_code=400, detail=f"该读者有 {unpaid} 笔未缴纳逾期罚款，请先结算清缴")

    # 检查借阅上限
    cur_count = db.query(BorrowRecord).filter(BorrowRecord.user_id == reader.id, BorrowRecord.return_date.is_(None)).count()
    if cur_count >= reader.max_borrow_limit:
        raise HTTPException(status_code=400, detail=f"已达该读者最大借阅限额({reader.max_borrow_limit}本)，请先还书")

    # 查找图书单册
    copy = db.query(BookCopy).filter(BookCopy.barcode == circ.barcode).first()
    if not copy:
        raise HTTPException(status_code=404, detail=f"未找到条码为 {circ.barcode} 的图书实体册")
    if copy.status != "available":
        raise HTTPException(status_code=400, detail=f"该单册当前状态为 [{copy.status}]，不可借出")

    book = db.query(Book).filter(Book.id == copy.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="关联主书目不存在")

    # 读取借期配置
    days_str = get_setting_val(db, "default_borrow_days", "30")
    borrow_days = int(days_str) if days_str.isdigit() else 30

    now = datetime.now()
    due_date = now + timedelta(days=borrow_days)

    record = BorrowRecord(
        user_id=reader.id,
        book_id=book.id,
        copy_id=copy.id,
        borrow_date=now,
        due_date=due_date,
        renew_count=0,
        status="borrowed",
        librarian_id=current_user.id,
        notes=f"前台服务台办理 (经办人: {current_user.username})"
    )

    copy.status = "borrowed"
    book.available_copies = max(0, book.available_copies - 1)
    book.borrow_count += 1

    db.add(record)
    db.commit()
    db.refresh(record)

    record_audit(db, current_user, "CIRC_BORROW", "BORROW", str(record.id), f"为读者 {reader.full_name} 借出图书《{book.title}》(条码: {copy.barcode})", request)
    return record

@app.post("/api/circulation/return", response_model=BorrowRecordResponse)
def quick_return(
    circ: QuickCirculationReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None
):
    """服务台快速还书：支持扫单册条形码或输入借阅单号"""
    record = None
    if circ.barcode:
        copy = db.query(BookCopy).filter(BookCopy.barcode == circ.barcode).first()
        if not copy:
            raise HTTPException(status_code=404, detail=f"未识别条形码: {circ.barcode}")
        record = db.query(BorrowRecord).filter(
            BorrowRecord.copy_id == copy.id,
            BorrowRecord.return_date.is_(None)
        ).first()
    elif circ.record_id:
        record = db.query(BorrowRecord).filter(BorrowRecord.id == circ.record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="未找到正在流转的未还借阅记录")
    if record.return_date:
        raise HTTPException(status_code=400, detail="该借阅记录已于较早前归还")

    now = datetime.now()
    record.return_date = now
    record.status = "returned"

    # 更新单册与主书目
    if record.copy:
        record.copy.status = "available"
    if record.book:
        record.book.available_copies += 1

    # 逾期罚金自动核算
    rate_str = get_setting_val(db, "daily_fine_rate", "0.50")
    rate = Decimal(rate_str)
    fine_record = None

    if now > record.due_date:
        overdue_days = (now - record.due_date).days
        if overdue_days > 0:
            fine_amount = Decimal(str(overdue_days)) * rate
            fine_record = FineRecord(
                user_id=record.user_id,
                borrow_id=record.id,
                amount=fine_amount,
                reason="overdue",
                status="unpaid",
                notes=f"图书《{record.book.title}》逾期 {overdue_days} 天，系统按 {rate:.2f} 元/天自动生成罚款单"
            )
            db.add(fine_record)

    db.commit()
    db.refresh(record)

    audit_msg = f"归还图书《{record.book.title}》成功"
    if fine_record:
        audit_msg += f"，产生逾期罚款 {fine_record.amount:.2f} 元"
    record_audit(db, current_user, "CIRC_RETURN", "BORROW", str(record.id), audit_msg, request)

    return record

@app.post("/api/circulation/renew/{record_id}", response_model=BorrowRecordResponse)
def renew_book(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """读者自主在线续借 或 管理员代办续借"""
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="借阅记录不存在")

    # 读者只能续借自己的书
    if current_user.role == "reader" and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作其他读者的借阅记录")

    if record.return_date:
        raise HTTPException(status_code=400, detail="图书已归还，无法续借")

    max_renew_str = get_setting_val(db, "max_renew_times", "2")
    max_renew = int(max_renew_str) if max_renew_str.isdigit() else 2

    if record.renew_count >= max_renew:
        raise HTTPException(status_code=400, detail=f"已达最大允许续借次数({max_renew}次)")

    # 逾期图书不可自助续借
    if datetime.now() > record.due_date:
        raise HTTPException(status_code=400, detail="该图书已逾期，请前往服务台缴清罚金后归还")

    extend_days_str = get_setting_val(db, "renew_days", "15")
    extend_days = int(extend_days_str) if extend_days_str.isdigit() else 15

    record.due_date = record.due_date + timedelta(days=extend_days)
    record.renew_count += 1
    db.commit()
    db.refresh(record)
    return record

# ==========================================
# 6. 借阅流水查询中心
# ==========================================

@app.get("/api/borrows", response_model=List[BorrowRecordResponse])
def list_borrow_records(
    status_filter: Optional[str] = None, # borrowed, returned, overdue
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(BorrowRecord)

    # 读者仅能查询自己
    if current_user.role == "reader":
        query = query.filter(BorrowRecord.user_id == current_user.id)
    elif user_id:
        query = query.filter(BorrowRecord.user_id == user_id)

    now = datetime.now()
    if status_filter == "borrowed":
        query = query.filter(BorrowRecord.return_date.is_(None), BorrowRecord.due_date >= now)
    elif status_filter == "overdue":
        query = query.filter(BorrowRecord.return_date.is_(None), BorrowRecord.due_date < now)
    elif status_filter == "returned":
        query = query.filter(BorrowRecord.return_date.isnot(None))

    if search:
        s = f"%{search}%"
        query = query.join(Book).filter(
            or_(
                Book.title.like(s),
                Book.isbn.like(s)
            )
        )

    records = query.order_by(desc(BorrowRecord.borrow_date)).offset(skip).limit(limit).all()
    
    rate_str = get_setting_val(db, "daily_fine_rate", "0.50")
    rate = Decimal(rate_str)
    for r in records:
        enrich_borrow_record(r, rate)

    return records

@app.get("/api/borrows/my", response_model=List[BorrowRecordResponse])
def list_my_borrows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    records = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == current_user.id
    ).order_by(desc(BorrowRecord.borrow_date)).all()

    rate_str = get_setting_val(db, "daily_fine_rate", "0.50")
    rate = Decimal(rate_str)
    for r in records:
        enrich_borrow_record(r, rate)

    return records

# ==========================================
# 7. 图书预约排队
# ==========================================

@app.get("/api/reservations", response_model=List[ReservationResponse])
def list_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Reservation)
    if current_user.role == "reader":
        query = query.filter(Reservation.user_id == current_user.id)
    return query.order_by(desc(Reservation.reserve_date)).all()

@app.post("/api/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    res_in: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    book = db.query(Book).filter(Book.id == res_in.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    if book.available_copies > 0:
        raise HTTPException(status_code=400, detail="该图书在架尚有余量，请直接前往书架取书借阅，无需预约")

    # 检查是否已预约
    exist = db.query(Reservation).filter(
        Reservation.user_id == current_user.id,
        Reservation.book_id == res_in.book_id,
        Reservation.status.in_(["waiting", "notified"])
    ).first()
    if exist:
        raise HTTPException(status_code=400, detail="您已预约过该图书，正在队列中等待到书")

    now = datetime.now()
    res = Reservation(
        user_id=current_user.id,
        book_id=res_in.book_id,
        reserve_date=now,
        expire_date=now + timedelta(days=7),
        status="waiting"
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res

@app.post("/api/reservations/{res_id}/cancel")
def cancel_reservation(
    res_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = db.query(Reservation).filter(Reservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if current_user.role == "reader" and res.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作他人预约")

    res.status = "cancelled"
    db.commit()
    return {"message": "预约已成功取消"}

# ==========================================
# 8. 罚金与费用结算管理
# ==========================================

@app.get("/api/fines", response_model=List[FineRecordResponse])
def list_fines(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(FineRecord)
    if current_user.role == "reader":
        query = query.filter(FineRecord.user_id == current_user.id)
    if status_filter:
        query = query.filter(FineRecord.status == status_filter)
    return query.order_by(desc(FineRecord.created_at)).all()

@app.post("/api/fines/{fine_id}/pay", response_model=FineRecordResponse)
def settle_fine(
    fine_id: int,
    pay_req: FinePayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None
):
    fine = db.query(FineRecord).filter(FineRecord.id == fine_id).first()
    if not fine:
        raise HTTPException(status_code=404, detail="未找到该罚金账单")
    if fine.status != "unpaid":
        raise HTTPException(status_code=400, detail="该账单已结清或已减免")

    if pay_req.waive:
        fine.status = "waived"
        fine.notes = f"管理员 {current_user.username} 予以特批减免: {pay_req.notes or '关怀政策'}"
    else:
        fine.status = "paid"
        fine.paid_at = datetime.now()
        fine.notes = f"服务台前台实收结算: {pay_req.notes or '现金/移动支付扫码'}"

    db.commit()
    db.refresh(fine)
    record_audit(db, current_user, "FINE_SETTLE", "FINE", str(fine.id), f"处理罚金账单: {fine.status} ({fine.amount:.2f}元)", request)
    return fine

# ==========================================
# 9. 读者档案与借阅卡管理 (Admin / Librarian)
# ==========================================

@app.get("/api/readers", response_model=List[UserResponse])
def list_readers(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian)
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
                User.phone.like(s)
            )
        )
    return query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()

@app.post("/api/readers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_reader_by_admin(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None
):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="电子邮箱已存在")

    card_number = user_in.card_number or f"CARD-{datetime.now().strftime('%Y%m')}{db.query(User).count() + 101:03d}"
    if db.query(User).filter(User.card_number == card_number).first():
        raise HTTPException(status_code=400, detail="借书卡号已存在")

    # 只有系统管理员能创建管理员/图书员角色
    role = user_in.role or "reader"
    if role in ["admin", "librarian"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅系统管理员有权指派管理员或图书员角色")

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
        status=user_in.status or "active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    record_audit(db, current_user, "CREATE_READER", "USER", str(new_user.id), f"录入新读者: {new_user.username} ({new_user.card_number})", request)
    return new_user

@app.put("/api/readers/{reader_id}", response_model=UserResponse)
def update_reader(
    reader_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian)
):
    reader = db.query(User).filter(User.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="读者不存在")

    if user_in.role and user_in.role != reader.role:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="仅系统管理员有权修改用户角色")
        reader.role = user_in.role

    if user_in.full_name:
        reader.full_name = user_in.full_name
    if user_in.phone is not None:
        reader.phone = user_in.phone
    if user_in.status:
        reader.status = user_in.status
    if user_in.max_borrow_limit is not None:
        reader.max_borrow_limit = user_in.max_borrow_limit
    if user_in.balance is not None:
        reader.balance = user_in.balance
    if user_in.password:
        reader.hashed_password = get_password_hash(user_in.password)

    db.commit()
    db.refresh(reader)
    return reader

@app.post("/api/readers/{reader_id}/reset-password")
def reset_reader_password(
    reader_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian)
):
    reader = db.query(User).filter(User.id == reader_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="读者不存在")

    # 默认重置为 123456
    reader.hashed_password = get_password_hash("123456")
    db.commit()
    record_audit(db, current_user, "RESET_PWD", "USER", str(reader.id), f"重置读者 {reader.username} 密码为默认 123456")
    return {"message": f"读者 {reader.username} 的密码已成功重置为 123456"}

# ==========================================
# 10. 公告广播与通知
# ==========================================

@app.get("/api/announcements", response_model=List[AnnouncementResponse])
def list_announcements(db: Session = Depends(get_db)):
    return db.query(Announcement).filter(Announcement.is_active == True).order_by(desc(Announcement.created_at)).all()

@app.post("/api/announcements", response_model=AnnouncementResponse)
def create_announcement(
    ann: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian)
):
    new_ann = Announcement(
        title=ann.title,
        content=ann.content,
        priority=ann.priority or "normal",
        is_active=ann.is_active if ann.is_active is not None else True,
        author_id=current_user.id
    )
    db.add(new_ann)
    db.commit()
    db.refresh(new_ann)
    return new_ann

@app.delete("/api/announcements/{ann_id}")
def delete_announcement(
    ann_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if ann:
        db.delete(ann)
        db.commit()
    return {"message": "公告已删除"}

# ==========================================
# 11. 全局系统设置与审计日志 (Admin Only)
# ==========================================

@app.get("/api/settings", response_model=List[SettingResponse])
def get_system_settings(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return db.query(SystemSetting).all()

@app.put("/api/settings/{setting_key}", response_model=SettingResponse)
def update_system_setting(
    setting_key: str,
    val_in: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    s = db.query(SystemSetting).filter(SystemSetting.setting_key == setting_key).first()
    if not s:
        s = SystemSetting(setting_key=setting_key, setting_value=val_in.setting_value, description="自定义设置")
        db.add(s)
    else:
        s.setting_value = val_in.setting_value
    db.commit()
    db.refresh(s)
    record_audit(db, current_user, "UPDATE_SETTING", "SETTINGS", setting_key, f"更新规则 {setting_key}={val_in.setting_value}")
    return s

@app.get("/api/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return db.query(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

# ==========================================
# 12. 前端静态资源托管（打包产物 frontend/dist）
# ==========================================
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    _ASSETS_DIR = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(_ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        """SPA 路由回退：非 /api 路径统一返回 index.html"""
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="接口不存在")
        candidate = os.path.realpath(os.path.join(FRONTEND_DIST, full_path))
        if full_path and candidate.startswith(FRONTEND_DIST) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
