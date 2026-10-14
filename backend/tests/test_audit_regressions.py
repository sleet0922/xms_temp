"""回归测试：覆盖功能审计中定位到的缺陷，防止再次退化

对应问题清单：
  1. GET /api/books/{id} 抛 NameError 导致详情页 500
  2. 逾期还书重复生成罚金单（重复计费）
  3. 预约流程无法闭环（fulfilled 状态不可达、已到馆不能取消）
  5. 「借阅上限」系统设置不生效（死配置）
  6. 「图书馆名称」系统设置不生效（死配置）
  10. 还书响应不携带罚金金额
  11. 借阅流水检索不支持按读者姓名/卡号
  9. 单册补录接口 body 冗余要求 book_id
"""
from datetime import datetime, timedelta
from decimal import Decimal

from models import (
    Book, BookCopy, BorrowRecord, FineRecord, Notification, Reservation, User,
)


def _reader(db, username) -> User:
    return db.query(User).filter(User.username == username).first()


def _notified_reservation(db, user, book_id) -> Reservation:
    res = Reservation(
        user_id=user.id,
        book_id=book_id,
        reserve_date=datetime.now(),
        expire_date=datetime.now() + timedelta(days=7),
        status="notified",
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res


# --------------------------------------------------------------------------- #
# 1. 图书详情接口
# --------------------------------------------------------------------------- #
def test_book_detail_returns_payload(client, db, reader_headers):
    """曾经因 copy_in 未定义直接 500，导致详情页与读者自助借阅全不可用"""
    book = db.query(Book).first()
    resp = client.get(f"/api/books/{book.id}", headers=reader_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == book.id
    assert body["title"] == book.title
    # 不存在的书目仍然是 404，语义不能被混淆
    assert client.get("/api/books/999999", headers=reader_headers).status_code == 404


# --------------------------------------------------------------------------- #
# 2. 逾期罚金唯一性
# --------------------------------------------------------------------------- #
def test_return_creates_exactly_one_fine(client, db, librarian_headers, overdue_record):
    assert db.query(FineRecord).filter(FineRecord.borrow_id == overdue_record.id).count() == 0

    resp = client.post("/api/circulation/return", headers=librarian_headers,
                       json={"record_id": overdue_record.id})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # 归还响应直接携带逾期天数与最终罚金，前端无需反查
    assert body["overdue_days"] >= 1
    assert Decimal(str(body["calculated_fine"])) > 0

    fines = db.query(FineRecord).filter(FineRecord.borrow_id == overdue_record.id).all()
    assert len(fines) == 1
    assert fines[0].amount == Decimal(str(body["calculated_fine"]))

    # 重复归还被拒绝，且不会追加第二张罚金单
    again = client.post("/api/circulation/return", headers=librarian_headers,
                        json={"record_id": overdue_record.id})
    assert again.status_code == 400
    assert db.query(FineRecord).filter(FineRecord.borrow_id == overdue_record.id).count() == 1


def test_return_reuses_preexisting_fine(client, db, librarian_headers, overdue_record):
    """逾期期间已预生成的账单，归还时应更新金额而不是再开一张"""
    db.add(FineRecord(
        user_id=overdue_record.user_id, borrow_id=overdue_record.id,
        amount=Decimal("1.00"), reason="overdue", status="unpaid", notes="逾期期间预生成",
    ))
    db.commit()

    resp = client.post("/api/circulation/return", headers=librarian_headers,
                       json={"record_id": overdue_record.id})
    assert resp.status_code == 200, resp.text

    fines = db.query(FineRecord).filter(FineRecord.borrow_id == overdue_record.id).all()
    assert len(fines) == 1
    assert fines[0].amount == Decimal(str(resp.json()["calculated_fine"]))
    assert fines[0].amount > Decimal("1.00")
    assert "归还时按" in (fines[0].notes or "")


def test_settled_fine_is_not_recreated(client, db, librarian_headers, overdue_record):
    """已结清的账单不再重复开单"""
    db.add(FineRecord(
        user_id=overdue_record.user_id, borrow_id=overdue_record.id,
        amount=Decimal("5.00"), reason="overdue", status="paid", notes="已结清",
    ))
    db.commit()

    resp = client.post("/api/circulation/return", headers=librarian_headers,
                       json={"record_id": overdue_record.id})
    assert resp.status_code == 200

    fines = db.query(FineRecord).filter(FineRecord.borrow_id == overdue_record.id).all()
    assert len(fines) == 1
    assert fines[0].status == "paid"
    assert fines[0].amount == Decimal("5.00")


# --------------------------------------------------------------------------- #
# 3. 预约闭环
# --------------------------------------------------------------------------- #
def test_reservation_fulfill_closes_loop(client, db, librarian_headers):
    reader = _reader(db, "student")
    copy = db.query(BookCopy).filter(BookCopy.status == "available").first()
    res = _notified_reservation(db, reader, copy.book_id)

    resp = client.post(f"/api/reservations/{res.id}/fulfill", headers=librarian_headers)
    assert resp.status_code == 201, resp.text
    record = resp.json()
    assert record["user_id"] == reader.id
    assert record["book_id"] == copy.book_id
    assert record["status"] == "borrowed"

    db.refresh(res)
    assert res.status == "fulfilled"  # 曾经不可达的状态现在可以推进

    # 读者收到兑现通知
    assert db.query(Notification).filter(
        Notification.user_id == reader.id,
        Notification.category == "reservation_fulfilled",
    ).count() == 1

    # 已兑现的预约不能重复办理
    assert client.post(f"/api/reservations/{res.id}/fulfill", headers=librarian_headers).status_code == 400


def test_reservation_fulfill_requires_stock(client, db, librarian_headers):
    reader = _reader(db, "student")
    book = db.query(Book).filter(Book.available_copies > 0).first()
    db.query(BookCopy).filter(BookCopy.book_id == book.id).update({BookCopy.status: "borrowed"})
    book.available_copies = 0
    db.commit()

    res = _notified_reservation(db, reader, book.id)
    resp = client.post(f"/api/reservations/{res.id}/fulfill", headers=librarian_headers)
    assert resp.status_code == 400
    db.refresh(res)
    assert res.status == "notified"  # 失败时预约状态不被破坏


def test_notified_reservation_can_be_cancelled(client, db, reader_headers):
    """「已到馆」的预约此前无法取消，读者会被卡死"""
    reader = _reader(db, "student")
    copy = db.query(BookCopy).filter(BookCopy.status == "available").first()
    res = _notified_reservation(db, reader, copy.book_id)

    resp = client.post(f"/api/reservations/{res.id}/cancel", headers=reader_headers)
    assert resp.status_code == 200, resp.text
    db.refresh(res)
    assert res.status == "cancelled"

    # 已结束的预约不能再次取消
    assert client.post(f"/api/reservations/{res.id}/cancel", headers=reader_headers).status_code == 400


def test_cancelling_notified_reservation_promotes_next(client, db, librarian_headers):
    """取消已到馆预约后，队列下一位读者应被顺延到「已到馆」"""
    first = _reader(db, "student")
    second = _reader(db, "lisi")
    copy = db.query(BookCopy).filter(BookCopy.status == "available").first()

    res1 = Reservation(user_id=first.id, book_id=copy.book_id,
                       reserve_date=datetime.now() - timedelta(days=2),
                       expire_date=datetime.now() + timedelta(days=7), status="notified")
    res2 = Reservation(user_id=second.id, book_id=copy.book_id,
                       reserve_date=datetime.now() - timedelta(days=1),
                       expire_date=datetime.now() + timedelta(days=7), status="waiting")
    db.add_all([res1, res2])
    db.commit()
    db.refresh(res1)
    db.refresh(res2)

    assert client.post(f"/api/reservations/{res1.id}/cancel", headers=librarian_headers).status_code == 200
    db.refresh(res1)
    db.refresh(res2)
    assert res1.status == "cancelled"
    assert res2.status == "notified"


# --------------------------------------------------------------------------- #
# 5/6. 系统设置真正生效
# --------------------------------------------------------------------------- #
def test_max_borrow_books_setting_takes_effect(client, db, admin_headers):
    """「借阅上限」此前是死配置：改设置对现有读者与新注册读者都无影响"""
    admin_limit_before = _reader(db, "admin").max_borrow_limit

    resp = client.put("/api/settings/max_borrow_books", headers=admin_headers,
                      json={"setting_value": "2"})
    assert resp.status_code == 200

    # 现有普通读者同步生效
    for name in ("student", "zhangsan", "lisi"):
        assert _reader(db, name).max_borrow_limit == 2
    # 管理员/馆员不受「普通读者」规则影响
    assert _reader(db, "admin").max_borrow_limit == admin_limit_before

    # 借阅限额校验随即以 2 为准：lisi 当前在借 2 本，应被拒绝
    lisi = _reader(db, "lisi")
    copy = db.query(BookCopy).filter(BookCopy.status == "available").first()
    resp = client.post("/api/circulation/borrow", headers=admin_headers,
                       json={"card_number": lisi.card_number, "barcode": copy.barcode})
    assert resp.status_code == 400, resp.text
    assert "最大借阅限额(2本)" in resp.json()["detail"]

    # 新注册读者也使用设置值
    resp = client.post("/api/auth/register", json={
        "username": "newbie01", "full_name": "新读者", "email": "newbie01@test.com",
        "password": "Test123456", "card_number": "CARD-880001",
    })
    assert resp.status_code in (200, 201), resp.text
    assert _reader(db, "newbie01").max_borrow_limit == 2


def test_library_name_exposed_by_public_config(client, db, admin_headers):
    """馆名此前写死在前端，改设置无任何效果"""
    assert client.put("/api/settings/library_name", headers=admin_headers,
                      json={"setting_value": "测试图书馆"}).status_code == 200

    resp = client.get("/api/system/config")  # 公开接口，无需登录
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["library_name"] == "测试图书馆"
    assert body["rules"]["max_renew_times"] == 2
    assert body["rules"]["daily_fine_rate"] == "0.50"


def test_public_config_does_not_leak_settings(client):
    """公开配置只暴露馆名与规则，不含审计等敏感信息"""
    body = client.get("/api/system/config").json()
    assert set(body.keys()) == {"library_name", "rules"}


# --------------------------------------------------------------------------- #
# 11. 借阅流水检索
# --------------------------------------------------------------------------- #
def test_borrow_search_matches_reader_name_and_card(client, db, librarian_headers):
    resp = client.get("/api/borrows", headers=librarian_headers,
                      params={"status_filter": "unreturned", "search": "张三"})
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert rows
    assert all("张三" in r["user"]["full_name"] for r in rows)

    resp = client.get("/api/borrows", headers=librarian_headers,
                      params={"search": "CARD-202603"})
    assert resp.status_code == 200
    rows = resp.json()
    assert rows
    assert all(r["user"]["card_number"] == "CARD-202603" for r in rows)

    # 书名检索仍然可用
    resp = client.get("/api/borrows", headers=librarian_headers, params={"search": "三体"})
    assert resp.status_code == 200
    assert all("三体" in r["book"]["title"] for r in resp.json())


# --------------------------------------------------------------------------- #
# 9. 单册补录
# --------------------------------------------------------------------------- #
def test_add_copy_without_book_id_in_body(client, db, librarian_headers):
    book = db.query(Book).first()

    resp = client.post(f"/api/books/{book.id}/copies", headers=librarian_headers,
                       json={"barcode": "BK-TEST-0001", "location_note": "测试架位"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["barcode"] == "BK-TEST-0001"

    db.refresh(book)
    assert book.total_copies == db.query(BookCopy).filter(BookCopy.book_id == book.id).count()
    assert book.available_copies == db.query(BookCopy).filter(
        BookCopy.book_id == book.id, BookCopy.status == "available"
    ).count()

    # 条码重复被拒绝
    dup = client.post(f"/api/books/{book.id}/copies", headers=librarian_headers,
                      json={"barcode": "BK-TEST-0001"})
    assert dup.status_code == 400

    # 读者无权补录
    assert client.post(f"/api/books/{book.id}/copies", headers=None,
                       json={"barcode": "BK-TEST-0002"}).status_code == 401
