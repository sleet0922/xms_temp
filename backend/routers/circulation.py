"""智慧借还流通服务台与借阅流水、预约排队"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from auth import get_current_user, require_librarian
from config import settings
from database import get_db
from models import Book, BorrowRecord, Reservation, User
from schemas import (
    BorrowRecordResponse, QuickCirculationBorrow, QuickCirculationReturn,
    ReservationCreate, ReservationResponse,
)
from services.audit import get_rules
from services.circulation import (
    borrow_by_card, enrich_borrow_record, renew_record, return_by_barcode_or_record,
)

router = APIRouter(tags=["流通借还"])


@router.post("/api/circulation/borrow", response_model=BorrowRecordResponse, summary="服务台扫码借书")
def quick_borrow(
    circ: QuickCirculationBorrow,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    return borrow_by_card(db, circ.card_number, circ.barcode, current_user, request)


@router.post("/api/circulation/return", response_model=BorrowRecordResponse, summary="服务台扫码还书（自动核算罚金）")
def quick_return(
    circ: QuickCirculationReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    record, _fine = return_by_barcode_or_record(db, circ.barcode, circ.record_id, current_user, request)
    return record


@router.post("/api/circulation/renew/{record_id}", response_model=BorrowRecordResponse, summary="续借（读者自助 / 馆员代办）")
def renew_book(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    rules = get_rules(db)
    return renew_record(db, record, current_user, rules["max_renew_times"], rules["renew_days"])


@router.get("/api/borrows", response_model=List[BorrowRecordResponse], summary="借阅流水查询")
def list_borrow_records(
    status_filter: Optional[str] = None,
    user_id: Optional[int] = None,
    book_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(BorrowRecord)

    if current_user.role == "reader":
        query = query.filter(BorrowRecord.user_id == current_user.id)
    elif user_id:
        query = query.filter(BorrowRecord.user_id == user_id)
    if book_id:
        query = query.filter(BorrowRecord.book_id == book_id)

    now = datetime.now()
    if status_filter == "borrowed":
        query = query.filter(BorrowRecord.return_date.is_(None), BorrowRecord.due_date >= now)
    elif status_filter == "overdue":
        query = query.filter(BorrowRecord.return_date.is_(None), BorrowRecord.due_date < now)
    elif status_filter == "returned":
        query = query.filter(BorrowRecord.return_date.isnot(None))

    if search:
        s = f"%{search}%"
        query = query.join(Book).filter(or_(Book.title.like(s), Book.isbn.like(s)))

    records = query.order_by(desc(BorrowRecord.borrow_date)).offset(skip).limit(limit).all()

    rate = get_rules(db)["fine_rate"]
    for r in records:
        enrich_borrow_record(r, rate)
    return records


@router.get("/api/borrows/my", response_model=List[BorrowRecordResponse], summary="我的借阅记录")
def list_my_borrows(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = (
        db.query(BorrowRecord)
        .filter(BorrowRecord.user_id == current_user.id)
        .order_by(desc(BorrowRecord.borrow_date))
        .all()
    )
    rate = get_rules(db)["fine_rate"]
    for r in records:
        enrich_borrow_record(r, rate)
    return records


@router.get("/api/reservations", response_model=List[ReservationResponse], summary="预约列表")
def list_reservations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Reservation)
    if current_user.role == "reader":
        query = query.filter(Reservation.user_id == current_user.id)
    return query.order_by(desc(Reservation.reserve_date)).all()


@router.post("/api/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED, summary="预约排队")
def create_reservation(
    res_in: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == res_in.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    if book.available_copies > 0:
        raise HTTPException(status_code=400, detail="该图书在架尚有余量，请直接前往书架取书借阅，无需预约")

    exist = db.query(Reservation).filter(
        Reservation.user_id == current_user.id,
        Reservation.book_id == res_in.book_id,
        Reservation.status.in_(["waiting", "notified"]),
    ).first()
    if exist:
        raise HTTPException(status_code=400, detail="您已预约过该图书，正在队列中等待到书")

    now = datetime.now()
    res = Reservation(
        user_id=current_user.id,
        book_id=res_in.book_id,
        reserve_date=now,
        expire_date=now + timedelta(days=settings.reservation_expire_days),
        status="waiting",
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res


@router.post("/api/reservations/{res_id}/cancel", summary="取消预约")
def cancel_reservation(
    res_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = db.query(Reservation).filter(Reservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if current_user.role == "reader" and res.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作他人预约")

    res.status = "cancelled"
    db.commit()
    return {"message": "预约已成功取消"}