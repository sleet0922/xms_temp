"""智能推荐服务：基于借阅历史分类偏好 + 馆藏高分热门 + 新书上架三段式推荐"""
from typing import List

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from models import Book, BorrowRecord, Category, User


def _candidates(query, exclude_ids: set):
    if exclude_ids:
        query = query.filter(Book.id.notin_(exclude_ids))
    return query


def _score(book: Book, affinity: bool = False) -> float:
    rating = float(book.rating or 0)
    popular = min(book.borrow_count / 5.0, 6.0)
    return round(rating * 2 + popular + (2.0 if affinity else 0.0), 2)


def build_recommendations(db: Session, user: User, limit: int = 8) -> List[dict]:
    borrowed_ids = {bid for (bid,) in db.query(BorrowRecord.book_id).filter(BorrowRecord.user_id == user.id).all()}
    seen = set(borrowed_ids)
    items: List[dict] = []

    def add(book: Book, reason: str, affinity: bool = False) -> None:
        if book.id in seen:
            return
        seen.add(book.id)
        items.append({"book": book, "reason": reason, "score": _score(book, affinity)})

    # 1) 兴趣分类：取借阅次数最多的前 3 个分类，推荐同类高分书
    cat_stats = (
        db.query(Book.category_id, func.count(BorrowRecord.id).label("cnt"))
        .join(BorrowRecord, BorrowRecord.book_id == Book.id)
        .filter(BorrowRecord.user_id == user.id, Book.category_id.isnot(None))
        .group_by(Book.category_id)
        .order_by(desc("cnt"))
        .limit(3)
        .all()
    )
    for cat_id, _cnt in cat_stats:
        cat = db.query(Category).filter(Category.id == cat_id).first()
        rows = _candidates(
            db.query(Book).filter(Book.category_id == cat_id), seen
        ).order_by(desc(Book.rating), desc(Book.borrow_count)).limit(3).all()
        for b in rows:
            add(b, f"您常借「{cat.name if cat else '同类'}」图书，这本同样高分", affinity=True)
        if len(items) >= limit:
            return items[:limit]

    # 2) 馆藏高分热门兜底
    if len(items) < limit:
        rows = _candidates(db.query(Book), seen).order_by(
            desc(Book.rating), desc(Book.borrow_count)
        ).limit(limit - len(items)).all()
        for b in rows:
            add(b, "馆藏高分热门，读者评价领先")

    # 3) 新书上架兜底（馆藏量不足时）
    if len(items) < limit:
        rows = _candidates(db.query(Book), seen).order_by(desc(Book.created_at)).limit(
            limit - len(items)
        ).all()
        for b in rows:
            add(b, "最新入库新书，抢先阅读")

    return items[:limit]