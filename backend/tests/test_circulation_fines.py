"""借还流通与逾期罚金测试"""
from datetime import datetime, timedelta
from decimal import Decimal

from conftest import auth_headers
from models import Book, BookCopy, BorrowRecord, FineRecord, Notification, Reservation, User


def _reader(db, username):
    return db.query(User).filter(User.username == username).first()


def test_borrow_success_and_stock_sync(client, db, librarian_headers, available_copy):
    book = db.query(Book).filter(Book.id == available_copy.book_id).first()
    stock_before = book.available_copies

    resp = client.post("/api/circulation/borrow", headers=librarian_headers,
                       json={"card_number": "CARD-202601", "barcode": available_copy.barcode})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "borrowed"
    assert body["due_date"] > body["borrow_date"]

    db.refresh(available_copy)
    db.refresh(book)
    assert available_copy.status == "borrowed"
    assert book.available_copies == stock_before - 1
    assert book.borrow_count >= 1

    # 归还后库存与单册状态复原
    resp = client.post("/api/circulation/return", headers=librarian_headers,
                       json={"barcode": available_copy.barcode})
    assert resp.status_code == 200
    db.refresh(available_copy)
    db.refresh(book)
    assert available_copy.status == "available"
    assert book.available_copies == stock_before


def test_borrow_blocked_by_unpaid_fine(client, db, librarian_headers, available_copy):
    zhangsan = _reader(db, "zhangsan")
    assert db.query(FineRecord).filter(FineRecord.user_id == zhangsan.id, FineRecord.status == "unpaid").count() > 0

    resp = client.post("/api/circulation/borrow", headers=librarian_headers,
                       json={"card_number": zhangsan.card_number, "barcode": available_copy.barcode})
    assert resp.status_code == 400
    assert "罚款" in resp.json()["detail"]


def test_borrow_blocked_for_frozen_reader(client, db, librarian_headers, available_copy, frozen_reader):
    resp = client.post("/api/circulation/borrow", headers=librarian_headers,
                       json={"card_number": frozen_reader.card_number, "barcode": available_copy.barcode})
    assert resp.status_code == 403


def test_borrow_blocked_when_copy_unavailable(client, db, librarian_headers):
    borrowed_copy = db.query(BookCopy).filter(BookCopy.status == "borrowed").first()
    resp = client.post("/api/circulation/borrow", headers=librarian_headers,
                       json={"card_number": "CARD-202601", "barcode": borrowed_copy.barcode})
    assert resp.status_code == 400
    assert "不可借出" in resp.json()["detail"]


def test_borrow_blocked_by_limit(client, db, librarian_headers, available_copy):
    lisi = _reader(db, "lisi")
    lisi.max_borrow_limit = 1  # 该读者已有 2 本在借
    db.commit()

    resp = client.post("/api/circulation/borrow", headers=librarian_headers,
                       json={"card_number": lisi.card_number, "barcode": available_copy.barcode})
    assert resp.status_code == 400
    assert "限额" in resp.json()["detail"]


def test_borrow_unknown_card_or_barcode(client, librarian_headers):
    assert client.post("/api/circulation/borrow", headers=librarian_headers,
                       json={"card_number": "CARD-NOBODY", "barcode": "X"}).status_code == 404
    assert client.post("/api/circulation/borrow", headers=librarian_headers,
                       json={"card_number": "CARD-202601", "barcode": "NO-SUCH-BARCODE"}).status_code == 404


def test_return_overdue_creates_fine_and_notification(client, db, librarian_headers, overdue_record):
    overdue_days = (datetime.now() - overdue_record.due_date).days

    resp = client.post("/api/circulation/return", headers=librarian_headers,
                       json={"record_id": overdue_record.id})
    assert resp.status_code == 200

    fine = db.query(FineRecord).filter(FineRecord.borrow_id == overdue_record.id).first()
    assert fine is not None
    assert fine.status == "unpaid"
    assert fine.amount == Decimal(str(overdue_days)) * Decimal("0.50")

    note = (
        db.query(Notification)
        .filter(Notification.user_id == overdue_record.user_id, Notification.category == "fine")
        .first()
    )
    assert note is not None and "罚金" in note.title


def test_renew_extends_due_date(client, db, reader_headers):
    record = (
        db.query(BorrowRecord)
        .filter(BorrowRecord.user_id == _reader(db, "student").id, BorrowRecord.return_date.is_(None))
        .first()
    )
    due_before = record.due_date

    resp = client.post(f"/api/circulation/renew/{record.id}", headers=reader_headers)
    assert resp.status_code == 200
    assert resp.json()["renew_count"] == record.renew_count + 1
    assert datetime.fromisoformat(resp.json()["due_date"]) > due_before


def test_renew_blocked_after_max_times(client, db, reader_headers):
    record = (
        db.query(BorrowRecord)
        .filter(BorrowRecord.user_id == _reader(db, "student").id, BorrowRecord.return_date.is_(None))
        .first()
    )
    record.renew_count = 2  # 系统设置 max_renew_times = 2
    db.commit()

    resp = client.post(f"/api/circulation/renew/{record.id}", headers=reader_headers)
    assert resp.status_code == 400
    assert "最大允许续借次数" in resp.json()["detail"]


def test_renew_blocked_when_overdue(client, db, reader_headers, overdue_record):
    headers = auth_headers(client, "lisi")
    resp = client.post(f"/api/circulation/renew/{overdue_record.id}", headers=headers)
    assert resp.status_code == 400
    assert "逾期" in resp.json()["detail"]


def test_reader_cannot_renew_others_record(client, db, reader_headers):
    record = (
        db.query(BorrowRecord)
        .filter(BorrowRecord.user_id == _reader(db, "lisi").id, BorrowRecord.return_date.is_(None))
        .first()
    )
    resp = client.post(f"/api/circulation/renew/{record.id}", headers=reader_headers)
    assert resp.status_code == 403


def test_reservation_requires_zero_stock_and_can_cancel(client, db, reader_headers):
    book = db.query(Book).filter(Book.available_copies > 0).first()
    assert client.post("/api/reservations", headers=reader_headers,
                       json={"book_id": book.id}).status_code == 400

    book.available_copies = 0
    db.commit()

    created = client.post("/api/reservations", headers=reader_headers, json={"book_id": book.id})
    assert created.status_code == 201
    res_id = created.json()["id"]
    assert created.json()["status"] == "waiting"

    # 同一本书不可重复排队
    assert client.post("/api/reservations", headers=reader_headers,
                       json={"book_id": book.id}).status_code == 400

    assert client.post(f"/api/reservations/{res_id}/cancel", headers=reader_headers).status_code == 200
    db.refresh(db.query(Reservation).filter(Reservation.id == res_id).first())
    assert db.query(Reservation).filter(Reservation.id == res_id).first().status == "cancelled"


def test_return_notifies_first_waiter(client, db, librarian_headers):
    """归还后预约队列首位读者收到「到书」通知，预约状态转为 notified"""
    waiter = _reader(db, "lisi")
    book = db.query(Book).filter(Book.available_copies >= 1).first()
    copy = db.query(BookCopy).filter(BookCopy.book_id == book.id, BookCopy.status == "available").first()

    book.available_copies = 1
    db.add(Reservation(user_id=waiter.id, book_id=book.id, reserve_date=datetime.now(),
                       expire_date=datetime.now() + timedelta(days=7), status="waiting"))
    db.commit()

    borrowed = client.post("/api/circulation/borrow", headers=librarian_headers,
                           json={"card_number": "CARD-202601", "barcode": copy.barcode})
    assert borrowed.status_code == 200
    returned = client.post("/api/circulation/return", headers=librarian_headers,
                           json={"barcode": copy.barcode})
    assert returned.status_code == 200

    res = db.query(Reservation).filter(Reservation.user_id == waiter.id, Reservation.book_id == book.id).first()
    db.refresh(res)
    assert res.status == "notified"

    note = db.query(Notification).filter(
        Notification.user_id == waiter.id, Notification.category == "reservation_ready"
    ).first()
    assert note is not None


def test_fine_settle_and_waive(client, db, librarian_headers):
    fine = db.query(FineRecord).filter(FineRecord.status == "unpaid").first()
    assert fine is not None

    resp = client.post(f"/api/fines/{fine.id}/pay", headers=librarian_headers, json={"notes": "测试结清"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"
    assert resp.json()["paid_at"] is not None

    # 已结清账单不可重复处理
    assert client.post(f"/api/fines/{fine.id}/pay", headers=librarian_headers, json={}).status_code == 400


def test_fine_reminder_and_summary(client, db, librarian_headers):
    zhangsan = _reader(db, "zhangsan")
    resp = client.post(f"/api/fines/remind/{zhangsan.id}", headers=librarian_headers)
    assert resp.status_code == 200
    assert db.query(Notification).filter(
        Notification.user_id == zhangsan.id, Notification.title.like("%催缴%")
    ).count() == 1

    summary = client.get("/api/fines/summary", headers=librarian_headers).json()
    assert Decimal(str(summary["amount"]["unpaid"])) >= Decimal("2.50")