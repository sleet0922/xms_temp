"""站内通知服务：预约到书 / 到期提醒 / 逾期催还 / 罚金告知（幂等，重复调用不会产生重复通知）"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from models import Book, BorrowRecord, FineRecord, Notification, Reservation
from services.audit import get_rules


def _notified(db: Session, user_id: int, category: str, link: Optional[str]) -> bool:
    """同一事件（分类 + 跳转链接）只通知一次"""
    q = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.category == category,
    )
    if link:
        q = q.filter(Notification.link == link)
    else:
        q = q.filter(Notification.link.is_(None))
    return db.query(q.exists()).scalar()


def create_notification(
    db: Session,
    user_id: int,
    category: str,
    title: str,
    content: Optional[str] = None,
    link: Optional[str] = None,
    commit: bool = True,
) -> Notification:
    note = Notification(
        user_id=user_id, category=category, title=title, content=content, link=link
    )
    db.add(note)
    if commit:
        db.commit()
        db.refresh(note)
    return note


def expire_reservations(db: Session) -> int:
    """将超过保留期限的排队或待取预约标记为失效。"""
    now = datetime.now()
    expired = (
        db.query(Reservation)
        .filter(
            Reservation.status.in_(["waiting", "notified"]),
            Reservation.expire_date <= now,
        )
        .all()
    )
    for res in expired:
        res.status = "cancelled"
    if expired:
        db.commit()
    return len(expired)


def notify_reservation_ready(db: Session, book: Book) -> Optional[Reservation]:
    """图书归还后触发：队列首位读者的预约转为「到书待取」并通知"""
    if not book or book.available_copies <= 0:
        return None
    expire_reservations(db)
    rules = get_rules(db)
    res = (
        db.query(Reservation)
        .filter(Reservation.book_id == book.id, Reservation.status == "waiting")
        .order_by(Reservation.reserve_date)
        .first()
    )
    if not res:
        return None

    res.status = "notified"
    res.expire_date = datetime.now() + timedelta(days=rules["reservation_expire_days"])
    link = f"/reservations?res={res.id}"
    if not _notified(db, res.user_id, "reservation_ready", link):
        create_notification(
            db,
            res.user_id,
            "reservation_ready",
            f"预约到书：{book.title}",
            f"您预约的《{book.title}》已归还到馆，请在 {rules['reservation_expire_days']} 天内前往服务台办理借阅，逾期预约将自动失效。",
            link,
            commit=False,
        )
    db.commit()
    return res


def notify_fine_generated(db: Session, fine: FineRecord) -> None:
    if not fine or not fine.id:
        return
    link = f"/fines?fine={fine.id}"
    if _notified(db, fine.user_id, "fine", link):
        return
    create_notification(
        db,
        fine.user_id,
        "fine",
        f"产生逾期罚金 {fine.amount:.2f} 元",
        fine.notes or "系统自动核算生成罚金账单，请尽快前往服务台结清。",
        link,
    )


def sync_due_reminders(db: Session, user_id: Optional[int] = None) -> int:
    """扫描未归还借阅记录，幂等生成「即将到期」与「已逾期」提醒，返回新增条数"""
    now = datetime.now()
    deadline = now + timedelta(days=get_rules(db)["due_reminder_days"])

    query = db.query(BorrowRecord).filter(BorrowRecord.return_date.is_(None))
    if user_id is not None:
        query = query.filter(BorrowRecord.user_id == user_id)

    created = 0
    for rec in query.all():
        book_title = rec.book.title if rec.book else f"书目#{rec.book_id}"
        link = f"/borrows?record={rec.id}"
        if rec.due_date < now:
            overdue_days = max(1, (now - rec.due_date).days)
            if not _notified(db, rec.user_id, "overdue", link):
                create_notification(
                    db,
                    rec.user_id,
                    "overdue",
                    f"《{book_title}》已逾期 {overdue_days} 天",
                    f"应还日期 {rec.due_date:%Y-%m-%d}，请尽快归还并结清罚金，逾期期间按日累计滞纳金。",
                    link,
                    commit=False,
                )
                created += 1
        elif rec.due_date <= deadline:
            if not _notified(db, rec.user_id, "due_reminder", link):
                days_left = max(0, (rec.due_date - now).days)
                create_notification(
                    db,
                    rec.user_id,
                    "due_reminder",
                    f"《{book_title}》将在 {days_left} 天后到期",
                    f"应还日期 {rec.due_date:%Y-%m-%d}，可在线办理续借，也可前往服务台归还。",
                    link,
                    commit=False,
                )
                created += 1
    if created:
        db.commit()
    return created


def unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .count()
    )


def latest(db: Session, user_id: int, limit: int = 20):
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
        .all()
    )
