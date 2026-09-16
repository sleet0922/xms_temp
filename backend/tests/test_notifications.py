"""站内通知测试：到期提醒幂等、逾期催还、已读与删除"""
from datetime import datetime, timedelta

from conftest import auth_headers
from models import Book, BookCopy, BorrowRecord, Notification, User


def test_overdue_reminder_is_idempotent(client, db):
    zhangsan = db.query(User).filter(User.username == "zhangsan").first()
    headers = auth_headers(client, "zhangsan")
    overdue_records = db.query(BorrowRecord).filter(
        BorrowRecord.user_id == zhangsan.id,
        BorrowRecord.return_date.is_(None),
        BorrowRecord.due_date < datetime.now(),
    ).count()
    assert overdue_records == 1

    first = client.get("/api/notifications", headers=headers).json()
    second = client.get("/api/notifications", headers=headers).json()
    overdue_notes = [n for n in first if n["category"] == "overdue"]

    assert len(overdue_notes) == 1
    assert [n["id"] for n in first] == [n["id"] for n in second], "重复拉取不应产生重复通知"


def test_due_soon_reminder(client, db):
    reader = db.query(User).filter(User.username == "lisi").first()
    book = db.query(Book).filter(Book.available_copies >= 1).first()
    copy = db.query(BookCopy).filter(BookCopy.book_id == book.id, BookCopy.status == "available").first()
    copy.status = "borrowed"
    book.available_copies -= 1
    db.add(BorrowRecord(
        user_id=reader.id, book_id=book.id, copy_id=copy.id,
        borrow_date=datetime.now() - timedelta(days=28),
        due_date=datetime.now() + timedelta(days=2),  # 3 天提醒阈值内
        status="borrowed", notes="即将到期",
    ))
    db.commit()

    notes = client.get("/api/notifications", headers=auth_headers(client, "lisi")).json()
    assert any(n["category"] == "due_reminder" for n in notes)


def test_mark_read_and_read_all(client, db):
    zhangsan = db.query(User).filter(User.username == "zhangsan").first()
    headers = auth_headers(client, "zhangsan")
    notes = client.get("/api/notifications", headers=headers).json()
    assert notes

    note_id = notes[0]["id"]
    assert client.post(f"/api/notifications/{note_id}/read", headers=headers).json()["is_read"] is True

    resp = client.post("/api/notifications/read-all", headers=headers)
    assert resp.status_code == 200
    assert client.get("/api/notifications", headers=headers, params={"unread_only": True}).json() == []


def test_notification_isolation_and_delete(client, db):
    reader = db.query(User).filter(User.username == "zhangsan").first()
    headers = auth_headers(client, "zhangsan")

    db.add(Notification(user_id=reader.id, category="system", title="馆内主题活动通知", content="欢迎参加"))
    db.commit()
    note_id = db.query(Notification).filter(Notification.category == "system").first().id

    # 其他读者不可操作他人通知
    other = auth_headers(client, "student")
    assert client.post(f"/api/notifications/{note_id}/read", headers=other).status_code == 404
    assert client.delete(f"/api/notifications/{note_id}", headers=other).status_code == 200  # 幂等，不泄露他人数据

    # 本人可以正常已读与删除
    assert client.post(f"/api/notifications/{note_id}/read", headers=headers).json()["is_read"] is True
    assert client.delete(f"/api/notifications/{note_id}", headers=headers).status_code == 200
    assert db.query(Notification).filter(Notification.id == note_id).first() is None