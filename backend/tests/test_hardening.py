"""边界回归：设置生效、权限隔离、唯一性和库存数据一致性。"""
from datetime import datetime, timedelta
from models import Book, BookCopy, Reservation, User


def test_librarian_updates_reader_email_but_cannot_touch_staff(client, db, librarian_headers):
    reader = db.query(User).filter(User.username == "student").first()
    response = client.put(
        f"/api/readers/{reader.id}",
        headers=librarian_headers,
        json={"email": "student-updated@future-lib.com"},
    )
    assert response.status_code == 200
    db.refresh(reader)
    assert reader.email == "student-updated@future-lib.com"

    admin = db.query(User).filter(User.username == "admin").first()
    assert client.put(
        f"/api/readers/{admin.id}",
        headers=librarian_headers,
        json={"full_name": "不应被馆员修改"},
    ).status_code == 403
    assert client.post(f"/api/readers/{admin.id}/reset-password", headers=librarian_headers).status_code == 403


def test_system_info_and_reminders_use_database_settings(client, db, admin_headers, reader_headers):
    assert client.put(
        "/api/settings/default_borrow_days", headers=admin_headers,
        json={"setting_value": "12"},
    ).status_code == 200
    assert client.put(
        "/api/settings/due_reminder_days", headers=admin_headers,
        json={"setting_value": "1"},
    ).status_code == 200
    info = client.get("/api/system/info", headers=admin_headers).json()
    assert info["rules"]["default_borrow_days"] == 12
    assert info["rules"]["due_reminder_days"] == 1

    reader = db.query(User).filter(User.username == "student").first()
    book = db.query(Book).filter(Book.available_copies > 0).first()
    copy = db.query(BookCopy).filter(BookCopy.book_id == book.id, BookCopy.status == "available").first()
    copy.status = "borrowed"
    book.available_copies -= 1
    from models import BorrowRecord
    db.add(BorrowRecord(
        user_id=reader.id, book_id=book.id, copy_id=copy.id,
        borrow_date=datetime.now(), due_date=datetime.now() + timedelta(hours=12),
        status="borrowed",
    ))
    db.commit()
    notes = client.get("/api/notifications", headers=reader_headers).json()
    assert any(note["category"] == "due_reminder" for note in notes)


def test_csv_handles_null_price_and_book_isbn_conflict(client, db, librarian_headers):
    first, second = db.query(Book).order_by(Book.id).limit(2).all()
    first.price = None
    db.commit()
    exported = client.get("/api/books-export")
    assert exported.status_code == 200
    assert "0.00" in exported.content.decode("utf-8-sig")
    assert client.put(
        f"/api/books/{second.id}", headers=librarian_headers,
        json={"isbn": first.isbn},
    ).status_code == 400


def test_expired_reservation_is_not_present_as_waiting(client, db, reader_headers):
    reader = db.query(User).filter(User.username == "student").first()
    book = db.query(Book).first()
    db.add(Reservation(
        user_id=reader.id, book_id=book.id,
        reserve_date=datetime.now() - timedelta(days=3),
        expire_date=datetime.now() - timedelta(days=1), status="waiting",
    ))
    db.commit()
    reservations = client.get("/api/reservations", headers=reader_headers).json()
    expired = [item for item in reservations if item["book_id"] == book.id and item["expire_date"] < datetime.now().isoformat()]
    assert expired and all(item["status"] == "cancelled" for item in expired)


def test_registration_rejects_duplicate_card_and_does_not_accept_custom_limit(client, db):
    payload = {
        "username": "new-reader", "email": "new-reader@future-lib.com",
        "full_name": "新读者", "password": "reader123", "card_number": "CARD-202601",
        "max_borrow_limit": 999,
    }
    assert client.post("/api/auth/register", json=payload).status_code == 400
    payload["card_number"] = "CARD-UNIQUE-001"
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["max_borrow_limit"] == 8
