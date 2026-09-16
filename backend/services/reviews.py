"""书评服务：评分回写书目聚合字段（平均分 + 评价人数）"""
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Book, Review


def recompute_book_rating(db: Session, book_id: int) -> None:
    """按未被隐藏的书评重算书目平均分与评价人数"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return
    avg_rating, cnt = (
        db.query(func.avg(Review.rating), func.count(Review.id))
        .filter(Review.book_id == book_id, Review.is_hidden.is_(False))
        .first()
    )
    book.rating_count = int(cnt or 0)
    if avg_rating is None:
        book.rating = Decimal("0.00")
    else:
        book.rating = Decimal(str(avg_rating)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    db.commit()


def visible_reviews(db: Session, book_id: int):
    return (
        db.query(Review)
        .filter(Review.book_id == book_id, Review.is_hidden.is_(False))
        .order_by(Review.updated_at.desc())
        .all()
    )