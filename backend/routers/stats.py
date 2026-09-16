"""统计报表与流通指标引擎：概览 / 走势 / 分类分布 / 热度榜 / 语言格式分布 / 活跃读者"""
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Book, BookCopy, BorrowRecord, Category, FineRecord, Reservation, Review, User
from schemas import StatsOverview
from services import notify

router = APIRouter(prefix="/api/stats", tags=["统计报表"])


@router.get("/overview", response_model=StatsOverview, summary="全局/个人概览指标")
def get_stats_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    total_books = db.query(Book).count()
    total_copies = db.query(BookCopy).count()
    total_readers = db.query(User).filter(User.role == "reader").count()
    active_borrows = db.query(BorrowRecord).filter(BorrowRecord.return_date.is_(None)).count()

    overdue_borrows = db.query(BorrowRecord).filter(
        BorrowRecord.return_date.is_(None), BorrowRecord.due_date < datetime.now()
    ).count()

    today_borrows = db.query(BorrowRecord).filter(BorrowRecord.borrow_date >= today_start).count()
    today_returns = db.query(BorrowRecord).filter(BorrowRecord.return_date >= today_start).count()

    unpaid_fines_sum = db.query(func.sum(FineRecord.amount)).filter(
        FineRecord.status == "unpaid"
    ).scalar() or Decimal("0.00")

    user_borrowed = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == current_user.id, BorrowRecord.return_date.is_(None)
    ).count()
    user_overdue = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.return_date.is_(None),
        BorrowRecord.due_date < datetime.now(),
    ).count()
    user_fines = db.query(func.sum(FineRecord.amount)).filter(
        FineRecord.user_id == current_user.id, FineRecord.status == "unpaid"
    ).scalar() or Decimal("0.00")

    total_reviews = db.query(Review).filter(Review.is_hidden.is_(False)).count()
    avg_rating = db.query(func.avg(Book.rating)).filter(Book.rating_count > 0).scalar()

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
        "user_fines": user_fines,
        "total_reviews": total_reviews,
        "avg_rating": Decimal(str(round(float(avg_rating), 2))) if avg_rating is not None else Decimal("0.00"),
        "total_reservations": db.query(Reservation).filter(
            Reservation.status.in_(["waiting", "notified"])
        ).count(),
        "unread_notifications": notify.unread_count(db, current_user.id),
    }


@router.get("/trends", summary="近 N 天借还走势")
def get_stats_trends(days: int = 15, db: Session = Depends(get_db)):
    timeline = []
    now = datetime.now()
    for i in range(days - 1, -1, -1):
        day_date = (now - timedelta(days=i)).date()
        day_start = datetime.combine(day_date, datetime.min.time())
        day_end = datetime.combine(day_date, datetime.max.time())

        borrow_cnt = db.query(BorrowRecord).filter(
            BorrowRecord.borrow_date >= day_start, BorrowRecord.borrow_date <= day_end
        ).count()
        return_cnt = db.query(BorrowRecord).filter(
            BorrowRecord.return_date >= day_start, BorrowRecord.return_date <= day_end
        ).count()

        timeline.append({
            "date": day_date.strftime("%m-%d"),
            "borrows": borrow_cnt,
            "returns": return_cnt,
        })
    return timeline


@router.get("/categories", summary="各分类藏书量")
def get_category_stats(db: Session = Depends(get_db)):
    results = []
    for cat in db.query(Category).all():
        results.append({
            "id": cat.id,
            "name": cat.name,
            "code": cat.code,
            "count": db.query(Book).filter(Book.category_id == cat.id).count(),
            "icon": cat.icon,
        })
    return results


@router.get("/popular-books", summary="借阅热度榜")
def get_popular_books(limit: int = 8, db: Session = Depends(get_db)):
    books = db.query(Book).order_by(desc(Book.borrow_count)).limit(limit).all()
    return [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "isbn": b.isbn,
            "cover_url": b.cover_url,
            "cover_file": b.cover_file,
            "borrow_count": b.borrow_count,
            "available_copies": b.available_copies,
            "rating": float(b.rating or 0),
        }
        for b in books
    ]


@router.get("/top-rated", summary="读者高分榜")
def get_top_rated_books(limit: int = 8, db: Session = Depends(get_db)):
    books = (
        db.query(Book)
        .filter(Book.rating_count > 0)
        .order_by(desc(Book.rating), desc(Book.rating_count))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "cover_url": b.cover_url,
            "cover_file": b.cover_file,
            "rating": float(b.rating or 0),
            "rating_count": b.rating_count,
        }
        for b in books
    ]


@router.get("/formats", summary="电子资源格式分布")
def get_format_stats(db: Session = Depends(get_db)):
    rows = (
        db.query(Book.format, func.count(Book.id), func.sum(Book.available_copies))
        .filter(Book.format.isnot(None), Book.format != "")
        .group_by(Book.format)
        .order_by(desc(func.count(Book.id)))
        .all()
    )
    return [
        {"format": fmt, "count": cnt, "available": int(avail or 0)}
        for fmt, cnt, avail in rows
    ]


@router.get("/languages", summary="语种分布")
def get_language_stats(db: Session = Depends(get_db)):
    rows = (
        db.query(Book.language, func.count(Book.id))
        .filter(Book.language.isnot(None), Book.language != "")
        .group_by(Book.language)
        .order_by(desc(func.count(Book.id)))
        .all()
    )
    return [{"language": lang, "count": cnt} for lang, cnt in rows]


@router.get("/active-readers", summary="读者活跃度排行")
def get_active_readers(limit: int = 10, db: Session = Depends(get_db)):
    rows = (
        db.query(
            User.id,
            User.full_name,
            User.card_number,
            func.count(BorrowRecord.id).label("borrow_total"),
        )
        .join(BorrowRecord, BorrowRecord.user_id == User.id)
        .group_by(User.id)
        .order_by(desc("borrow_total"))
        .limit(limit)
        .all()
    )
    result = []
    for uid, name, card, total in rows:
        active = db.query(BorrowRecord).filter(
            BorrowRecord.user_id == uid, BorrowRecord.return_date.is_(None)
        ).count()
        overdue = db.query(BorrowRecord).filter(
            BorrowRecord.user_id == uid,
            BorrowRecord.return_date.is_(None),
            BorrowRecord.due_date < datetime.now(),
        ).count()
        result.append({
            "user_id": uid,
            "full_name": name,
            "card_number": card,
            "borrow_total": total,
            "active_borrows": active,
            "overdue": overdue,
        })
    return result