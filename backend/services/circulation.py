"""流通服务：扫码借书 / 还书（自动罚金）/ 续借 / 逾期罚金核算"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from models import Book, BookCopy, BorrowRecord, FineRecord, User
from services.audit import get_rules, record_audit
from services import notify


def enrich_borrow_record(rec: BorrowRecord, daily_fine_rate: Decimal) -> BorrowRecord:
    """为借阅记录补充实时的逾期天数与应缴罚金（不落库，仅用于展示）"""
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


def ensure_reader_eligible(db: Session, reader: User) -> None:
    """借阅前置校验：冻结账户、未缴罚款、最大借阅限额"""
    if reader.status == "frozen":
        raise HTTPException(status_code=403, detail="该读者借书卡已被冻结，无法借阅")

    unpaid = db.query(FineRecord).filter(
        FineRecord.user_id == reader.id, FineRecord.status == "unpaid"
    ).count()
    if unpaid > 0:
        raise HTTPException(status_code=400, detail=f"该读者有 {unpaid} 笔未缴纳逾期罚款，请先结算清缴")

    cur_count = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == reader.id, BorrowRecord.return_date.is_(None)
    ).count()
    if cur_count >= reader.max_borrow_limit:
        raise HTTPException(status_code=400, detail=f"已达该读者最大借阅限额({reader.max_borrow_limit}本)，请先还书")


def borrow_by_card(
    db: Session,
    card_number: str,
    barcode: str,
    operator: User,
    request: Optional[Request] = None,
) -> BorrowRecord:
    """服务台快速扫码借书：借书卡号 + 单册条形码"""
    reader = db.query(User).filter(User.card_number == card_number).first()
    if not reader:
        raise HTTPException(status_code=404, detail=f"未找到借书卡号为 {card_number} 的读者")

    ensure_reader_eligible(db, reader)

    copy = db.query(BookCopy).filter(BookCopy.barcode == barcode).first()
    if not copy:
        raise HTTPException(status_code=404, detail=f"未找到条码为 {barcode} 的图书实体册")
    if copy.status != "available":
        raise HTTPException(status_code=400, detail=f"该单册当前状态为 [{copy.status}]，不可借出")

    book = db.query(Book).filter(Book.id == copy.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="关联主书目不存在")

    rules = get_rules(db)
    now = datetime.now()
    record = BorrowRecord(
        user_id=reader.id,
        book_id=book.id,
        copy_id=copy.id,
        borrow_date=now,
        due_date=now + timedelta(days=rules["borrow_days"]),
        renew_count=0,
        status="borrowed",
        librarian_id=operator.id,
        notes=f"前台服务台办理 (经办人: {operator.username})",
    )

    copy.status = "borrowed"
    book.available_copies = max(0, book.available_copies - 1)
    book.borrow_count += 1

    db.add(record)
    db.commit()
    db.refresh(record)

    record_audit(
        db, operator, "CIRC_BORROW", "BORROW", str(record.id),
        f"为读者 {reader.full_name} 借出图书《{book.title}》(条码: {copy.barcode})", request,
    )
    return record


def borrow_self(db: Session, reader: User, book_id: int, request: Optional[Request] = None) -> BorrowRecord:
    """读者在线自助借阅：校验借阅资格后自动分配一册在架复本"""
    ensure_reader_eligible(db, reader)

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在或已下架")

    copy = (
        db.query(BookCopy)
        .filter(BookCopy.book_id == book.id, BookCopy.status == "available")
        .first()
    )
    if not copy:
        raise HTTPException(status_code=400, detail="该图书暂无可借的在架复本，可先加入预约队列")

    rules = get_rules(db)
    now = datetime.now()
    record = BorrowRecord(
        user_id=reader.id,
        book_id=book.id,
        copy_id=copy.id,
        borrow_date=now,
        due_date=now + timedelta(days=rules["borrow_days"]),
        renew_count=0,
        status="borrowed",
        notes="读者在线自助借阅",
    )

    copy.status = "borrowed"
    book.available_copies = max(0, book.available_copies - 1)
    book.borrow_count += 1

    db.add(record)
    db.commit()
    db.refresh(record)

    record_audit(
        db, reader, "CIRC_SELF_BORROW", "BORROW", str(record.id),
        f"读者 {reader.full_name} 在线自助借阅《{book.title}》(条码: {copy.barcode})", request,
    )
    return record


def return_by_barcode_or_record(
    db: Session,
    barcode: Optional[str],
    record_id: Optional[int],
    operator: User,
    request: Optional[Request] = None,
) -> Tuple[BorrowRecord, Optional[FineRecord]]:
    """服务台快速还书：支持扫单册条形码或输入借阅单号，逾期自动生成罚金单"""
    record = None
    if barcode:
        copy = db.query(BookCopy).filter(BookCopy.barcode == barcode).first()
        if not copy:
            raise HTTPException(status_code=404, detail=f"未识别条形码: {barcode}")
        record = db.query(BorrowRecord).filter(
            BorrowRecord.copy_id == copy.id, BorrowRecord.return_date.is_(None)
        ).first()
    elif record_id:
        record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="未找到正在流转的未还借阅记录")
    if record.return_date:
        raise HTTPException(status_code=400, detail="该借阅记录已于较早前归还")

    now = datetime.now()
    record.return_date = now
    record.status = "returned"

    if record.copy:
        record.copy.status = "available"
    if record.book:
        record.book.available_copies += 1

    rate = get_rules(db)["fine_rate"]
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
                notes=f"图书《{record.book.title}》逾期 {overdue_days} 天，系统按 {rate:.2f} 元/天自动生成罚款单",
            )
            db.add(fine_record)

    db.commit()
    db.refresh(record)

    audit_msg = f"归还图书《{record.book.title}》成功"
    if fine_record:
        db.refresh(fine_record)
        notify.notify_fine_generated(db, fine_record)
        audit_msg += f"，产生逾期罚款 {fine_record.amount:.2f} 元"
    record_audit(db, operator, "CIRC_RETURN", "BORROW", str(record.id), audit_msg, request)

    # 归还后触发预约队列「到书通知」
    if record.book:
        notify.notify_reservation_ready(db, record.book)

    return record, fine_record


def renew_record(db: Session, record: BorrowRecord, operator: User, max_renew: int, extend_days: int) -> BorrowRecord:
    """续借：读者仅可续借本人记录，逾期或超次数将拒绝"""
    if operator.role == "reader" and record.user_id != operator.id:
        raise HTTPException(status_code=403, detail="无权操作其他读者的借阅记录")
    if record.return_date:
        raise HTTPException(status_code=400, detail="图书已归还，无法续借")
    if record.renew_count >= max_renew:
        raise HTTPException(status_code=400, detail=f"已达最大允许续借次数({max_renew}次)")
    if datetime.now() > record.due_date:
        raise HTTPException(status_code=400, detail="该图书已逾期，请前往服务台缴清罚金后归还")

    record.due_date = record.due_date + timedelta(days=extend_days)
    record.renew_count += 1
    db.commit()
    db.refresh(record)
    return record