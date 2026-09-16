"""内容与互动中心：公告广播 / 书评评分 / 智能推荐 / 站内通知"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin, require_librarian
from database import get_db
from models import Announcement, Book, Review, User
from schemas import (
    AnnouncementCreate, AnnouncementResponse, NotificationResponse,
    RecommendationItem, ReviewCreate, ReviewModerate, ReviewResponse, ReviewUpdate,
)
from services import notify
from services.recommend import build_recommendations
from services.reviews import recompute_book_rating

router = APIRouter(tags=["内容与互动"])


# ============ 公告广播 ============

@router.get("/api/announcements", response_model=List[AnnouncementResponse], summary="公告列表")
def list_announcements(db: Session = Depends(get_db)):
    return (
        db.query(Announcement)
        .filter(Announcement.is_active == True)  # noqa: E712
        .order_by(desc(Announcement.created_at))
        .all()
    )


@router.post("/api/announcements", response_model=AnnouncementResponse, summary="发布公告")
def create_announcement(
    ann: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    new_ann = Announcement(
        title=ann.title,
        content=ann.content,
        priority=ann.priority or "normal",
        is_active=ann.is_active if ann.is_active is not None else True,
        author_id=current_user.id,
    )
    db.add(new_ann)
    db.commit()
    db.refresh(new_ann)
    return new_ann


@router.delete("/api/announcements/{ann_id}", summary="删除公告")
def delete_announcement(
    ann_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if ann:
        db.delete(ann)
        db.commit()
    return {"message": "公告已删除"}


# ============ 书评与评分 ============

@router.get("/api/books/{book_id}/reviews", response_model=List[ReviewResponse], summary="某本书的读者书评")
def list_book_reviews(
    book_id: int,
    include_hidden: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Review).filter(Review.book_id == book_id)
    if not (include_hidden and current_user.role in ["admin", "librarian"]):
        query = query.filter(Review.is_hidden.is_(False))
    return query.order_by(desc(Review.updated_at)).all()


@router.post("/api/books/{book_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED,
             summary="发表/更新我的书评（每人每书一条）")
def upsert_review(
    book_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="评分需为 1~5 星")

    review = db.query(Review).filter(
        Review.user_id == current_user.id, Review.book_id == book_id
    ).first()
    if review:
        review.rating = payload.rating
        if payload.content is not None:
            review.content = payload.content
    else:
        review = Review(
            user_id=current_user.id,
            book_id=book_id,
            rating=payload.rating,
            content=payload.content,
        )
        db.add(review)
    db.commit()
    db.refresh(review)

    recompute_book_rating(db, book_id)
    return review


@router.get("/api/reviews/my", response_model=List[ReviewResponse], summary="我的书评")
def list_my_reviews(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .order_by(desc(Review.updated_at))
        .all()
    )


@router.get("/api/reviews", response_model=List[ReviewResponse], summary="书评管理列表（馆员）")
def list_all_reviews(
    book_id: Optional[int] = None,
    visible: Optional[bool] = None,
    skip: int = 0,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    query = db.query(Review)
    if book_id:
        query = query.filter(Review.book_id == book_id)
    if visible is not None:
        query = query.filter(Review.is_hidden.is_(not visible))
    return query.order_by(desc(Review.updated_at)).offset(skip).limit(limit).all()


@router.put("/api/reviews/{review_id}", response_model=ReviewResponse, summary="修改我的书评")
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="书评不存在")
    if review.user_id != current_user.id and current_user.role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="无权修改他人书评")

    if payload.rating is not None:
        if payload.rating < 1 or payload.rating > 5:
            raise HTTPException(status_code=400, detail="评分需为 1~5 星")
        review.rating = payload.rating
    if payload.content is not None:
        review.content = payload.content
    db.commit()
    db.refresh(review)

    recompute_book_rating(db, review.book_id)
    return review


@router.put("/api/reviews/{review_id}/visibility", response_model=ReviewResponse, summary="隐藏/恢复书评（馆员）")
def moderate_review(
    review_id: int,
    payload: ReviewModerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="书评不存在")
    review.is_hidden = payload.is_hidden
    db.commit()
    db.refresh(review)

    recompute_book_rating(db, review.book_id)
    db.refresh(review)
    return review


@router.delete("/api/reviews/{review_id}", summary="删除书评")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="书评不存在")
    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除他人书评")

    book_id = review.book_id
    db.delete(review)
    db.commit()
    recompute_book_rating(db, book_id)
    return {"message": "书评已删除"}


# ============ 智能推荐 ============

@router.get("/api/recommendations", response_model=List[RecommendationItem], summary="个性化图书推荐")
def get_recommendations(
    limit: int = Query(8, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_recommendations(db, current_user, limit)


@router.get("/api/books/{book_id}/similar", response_model=List[RecommendationItem], summary="同类高分图书")
def get_similar_books(
    book_id: int,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")

    query = db.query(Book).filter(Book.id != book.id)
    if book.category_id:
        query = query.filter(Book.category_id == book.category_id)
    rows = query.order_by(desc(Book.rating), desc(Book.borrow_count)).limit(limit).all()

    if len(rows) < limit:
        extra = (
            db.query(Book)
            .filter(Book.id != book.id, Book.id.notin_([b.id for b in rows]))
            .order_by(desc(Book.borrow_count))
            .limit(limit - len(rows))
            .all()
        )
        rows.extend(extra)

    return [{"book": b, "reason": "同类高分推荐", "score": float(b.rating or 0)} for b in rows]


# ============ 站内通知 ============

@router.get("/api/notifications", response_model=List[NotificationResponse], summary="我的通知（自动同步到期提醒）")
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notify.sync_due_reminders(db, current_user.id)
    query = db.query(notify.Notification).filter(notify.Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(notify.Notification.is_read.is_(False))
    return query.order_by(desc(notify.Notification.created_at)).limit(limit).all()


@router.post("/api/notifications/{note_id}/read", response_model=NotificationResponse, summary="标记通知已读")
def mark_notification_read(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(notify.Notification).filter(
        notify.Notification.id == note_id, notify.Notification.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="通知不存在")
    note.is_read = True
    db.commit()
    db.refresh(note)
    return note


@router.post("/api/notifications/read-all", summary="全部标记已读")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = (
        db.query(notify.Notification)
        .filter(notify.Notification.user_id == current_user.id, notify.Notification.is_read.is_(False))
        .update({notify.Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()
    return {"message": f"已将 {updated} 条通知标记为已读", "updated": updated}


@router.delete("/api/notifications/{note_id}", summary="删除通知")
def delete_notification(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(notify.Notification).filter(
        notify.Notification.id == note_id, notify.Notification.user_id == current_user.id
    ).first()
    if note:
        db.delete(note)
        db.commit()
    return {"message": "通知已删除"}