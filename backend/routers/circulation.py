"""智慧借还流通服务台与借阅流水、预约排队"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from auth import get_current_user, require_librarian
from database import get_db
from models import Book, BorrowRecord, Reservation, User
from schemas import (
    BorrowRecordResponse, QuickCirculationBorrow, QuickCirculationReturn,
    ReservationCreate, ReservationResponse, SelfBorrowRequest,
)
from services.audit import get_rules, record_audit
from services import notify
from services.circulation import (
    borrow_by_card, borrow_self, enrich_borrow_record, renew_record, return_by_barcode_or_record,
)

router = APIRouter(tags=["流通借还"])


@router.post("/api/circulation/borrow", response_model=BorrowRecordResponse, summary="服务台借书（扫条码或按书目自动分配复本）")
def quick_borrow(
    circ: QuickCirculationBorrow,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    return borrow_by_card(db, circ.card_number, circ.barcode, current_user, request, circ.book_id)


@router.post("/api/circulation/return", response_model=BorrowRecordResponse, summary="服务台扫码还书（自动核算罚金）")
def quick_return(
    circ: QuickCirculationReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    record, _fine = return_by_barcode_or_record(db, circ.barcode, circ.record_id, current_user, request)
    return record


@router.post("/api/circulation/return-requests/{record_id}/approve", response_model=BorrowRecordResponse, summary="管理员确认读者还书申请")
def approve_return_request(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if not record or record.return_date:
        raise HTTPException(status_code=404, detail="未找到可确认的借阅记录")
    if record.return_request_status != "pending":
        raise HTTPException(status_code=400, detail="该还书申请不在待确认状态")
    returned, _fine = return_by_barcode_or_record(db, None, record.id, current_user, request)
    returned.return_request_status = "approved"
    db.commit()
    db.refresh(returned)
    title = returned.book.title if returned.book else f"借阅记录 #{returned.id}"
    notify.create_notification(
        db, returned.user_id, "return_request_approved", "还书申请已确认",
        f"《{title}》已由管理员确认归还。",
        f"/borrows?record={returned.id}",
    )
    return returned


@router.post("/api/circulation/return-requests/{record_id}/reject", response_model=BorrowRecordResponse, summary="管理员驳回读者还书申请")
def reject_return_request(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if not record or record.return_date:
        raise HTTPException(status_code=404, detail="未找到可处理的借阅记录")
    if record.return_request_status != "pending":
        raise HTTPException(status_code=400, detail="该还书申请不在待处理状态")
    record.return_request_status = "rejected"
    db.commit()
    db.refresh(record)
    title = record.book.title if record.book else f"借阅记录 #{record.id}"
    notify.create_notification(
        db, record.user_id, "return_request_rejected", "还书申请未通过",
        f"《{title}》的还书申请已被驳回，请将图书交至服务台后重新申请。",
        f"/borrows?record={record.id}",
    )
    return record


@router.post(
    "/api/borrows/self",
    response_model=BorrowRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="读者在线自助借阅（自动分配在架复本）",
)
def self_borrow(
    payload: SelfBorrowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    return borrow_self(db, current_user, payload.book_id, request)


@router.post("/api/circulation/renew/{record_id}", response_model=BorrowRecordResponse, summary="续借（读者自助 / 馆员代办）")
def renew_book(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    rules = get_rules(db)
    return renew_record(db, record, current_user, rules["max_renew_times"], rules["renew_days"], request)


@router.post("/api/borrows/{record_id}/return-request", response_model=BorrowRecordResponse, summary="读者申请提前还书")
def request_return(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    if current_user.role == "reader" and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作他人的借阅记录")
    if record.return_date:
        raise HTTPException(status_code=400, detail="该图书已经归还")
    if record.return_request_status == "pending":
        raise HTTPException(status_code=400, detail="还书申请已提交，请等待管理员确认")

    record.return_request_status = "pending"
    record.return_requested_at = datetime.now()
    db.commit()
    db.refresh(record)
    book_title = record.book.title if record.book else f"借阅记录 #{record.id}"
    for librarian in db.query(User).filter(User.role.in_(["librarian", "admin"])).all():
        notify.create_notification(
            db, librarian.id, "return_request", "收到提前还书申请",
            f"{current_user.full_name} 申请归还《{book_title}》，请在借还工作台确认。",
            "/admin/circulation",
        )
    record_audit(db, current_user, "RETURN_REQUEST", "BORROW", str(record.id),
                 f"申请提前归还图书《{book_title}》", request)
    return record


@router.get("/api/borrows", response_model=List[BorrowRecordResponse], summary="借阅流水查询")
def list_borrow_records(
    status_filter: Optional[str] = None,
    user_id: Optional[int] = None,
    book_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
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
    if status_filter == "unreturned":
        # 服务台还书下拉：所有尚未归还的记录（含已逾期）
        query = query.filter(BorrowRecord.return_date.is_(None))
    elif status_filter == "return_requested":
        if current_user.role == "reader":
            query = query.filter(BorrowRecord.user_id == current_user.id)
        query = query.filter(BorrowRecord.return_date.is_(None), BorrowRecord.return_request_status == "pending")
    elif status_filter == "borrowed":
        query = query.filter(BorrowRecord.return_date.is_(None), BorrowRecord.due_date >= now)
    elif status_filter == "overdue":
        query = query.filter(BorrowRecord.return_date.is_(None), BorrowRecord.due_date < now)
    elif status_filter == "returned":
        query = query.filter(BorrowRecord.return_date.isnot(None))

    if search:
        s = f"%{search}%"
        query = (
            query.outerjoin(Book, BorrowRecord.book_id == Book.id)
            .outerjoin(User, BorrowRecord.user_id == User.id)
            .filter(or_(
                Book.title.like(s),
                Book.isbn.like(s),
                User.full_name.like(s),
                User.username.like(s),
                User.card_number.like(s),
            ))
        )

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
    notify.expire_reservations(db)
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
    notify.expire_reservations(db)
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
    rules = get_rules(db)
    res = Reservation(
        user_id=current_user.id,
        book_id=res_in.book_id,
        reserve_date=now,
        expire_date=now + timedelta(days=rules["reservation_expire_days"]),
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
    request: Request = None,
):
    res = db.query(Reservation).filter(Reservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if current_user.role == "reader" and res.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作他人预约")
    if res.status in ("cancelled", "fulfilled"):
        raise HTTPException(status_code=400, detail="该预约已结束，无需再次取消")

    was_notified = res.status == "notified"
    book = db.query(Book).filter(Book.id == res.book_id).first()
    res.status = "cancelled"
    db.commit()

    # 「已到馆」预约被取消后，释放出来的这册应顺延给队列下一位读者
    if was_notified and book:
        notify.notify_reservation_ready(db, book)

    record_audit(db, current_user, "RESERVATION_CANCEL", "RESERVATION", str(res.id),
                 f"取消预约《{book.title if book else res.book_id}》", request)
    return {"message": "预约已成功取消"}


@router.post(
    "/api/reservations/{res_id}/fulfill",
    response_model=BorrowRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="预约取书：为读者办理借出并兑现预约",
)
def fulfill_reservation(
    res_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
    request: Request = None,
):
    notify.expire_reservations(db)
    res = db.query(Reservation).filter(Reservation.id == res_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    if res.status not in ("waiting", "notified"):
        raise HTTPException(status_code=400, detail="该预约已结束，无法办理取书")

    book = db.query(Book).filter(Book.id == res.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="预约的图书不存在")
    if book.available_copies <= 0:
        raise HTTPException(status_code=400, detail="该书目暂无可借的在架复本，无法办理取书")

    reader = db.query(User).filter(User.id == res.user_id).first()
    if not reader:
        raise HTTPException(status_code=404, detail="预约读者不存在")

    record = borrow_by_card(db, reader.card_number, None, current_user, request, book.id)
    res.status = "fulfilled"
    db.commit()
    db.refresh(res)

    notify.create_notification(
        db,
        res.user_id,
        "reservation_fulfilled",
        f"预约已兑现：{book.title}",
        f"您预约的《{book.title}》已办理借出，应还日期 {record.due_date:%Y-%m-%d}，请按期归还。",
        f"/borrows?record={record.id}",
    )
    record_audit(db, current_user, "RESERVATION_FULFILL", "RESERVATION", str(res.id),
                 f"为读者 {reader.full_name} 办理预约取书《{book.title}》(借阅记录 #{record.id})", request)

    enrich_borrow_record(record, get_rules(db)["fine_rate"])
    return record
