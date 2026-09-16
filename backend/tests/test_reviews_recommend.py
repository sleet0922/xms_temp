"""书评评分与智能推荐测试"""
from decimal import Decimal

from conftest import auth_headers
from models import Book, BorrowRecord, Review, User


def _book(db):
    return db.query(Book).first()


def test_create_review_syncs_book_rating(client, db, admin_headers):
    book = _book(db)
    resp = client.post(f"/api/books/{book.id}/reviews", headers=admin_headers,
                       json={"rating": 5, "content": "非常值得一读"})
    assert resp.status_code == 201

    db.refresh(book)
    assert Decimal(book.rating) == Decimal("5.00")
    assert book.rating_count == 1


def test_second_review_averages_and_upsert_by_same_user(client, db, admin_headers):
    book = _book(db)
    client.post(f"/api/books/{book.id}/reviews", headers=admin_headers, json={"rating": 5})
    student = auth_headers(client, "student")
    client.post(f"/api/books/{book.id}/reviews", headers=student, json={"rating": 3, "content": "一般"})

    db.refresh(book)
    assert book.rating_count == 2
    assert Decimal(book.rating) == Decimal("4.00")

    # 同一读者重复提交为更新而非新增
    client.post(f"/api/books/{book.id}/reviews", headers=admin_headers, json={"rating": 1, "content": "改主意了"})
    db.refresh(book)
    assert db.query(Review).filter(Review.book_id == book.id).count() == 2
    assert book.rating_count == 2
    assert Decimal(book.rating) == Decimal("2.00")


def test_rating_bounds_rejected(client, db, admin_headers):
    book = _book(db)
    assert client.post(f"/api/books/{book.id}/reviews", headers=admin_headers, json={"rating": 0}).status_code == 400
    assert client.post(f"/api/books/{book.id}/reviews", headers=admin_headers, json={"rating": 6}).status_code == 400


def test_update_and_delete_own_review(client, db, reader_headers):
    book = _book(db)
    created = client.post(f"/api/books/{book.id}/reviews", headers=reader_headers, json={"rating": 4})
    review_id = created.json()["id"]

    updated = client.put(f"/api/reviews/{review_id}", headers=reader_headers, json={"rating": 2, "content": "重读后改观"})
    assert updated.status_code == 200
    assert updated.json()["rating"] == 2
    db.refresh(book)
    assert Decimal(book.rating) == Decimal("2.00")

    assert client.delete(f"/api/reviews/{review_id}", headers=reader_headers).status_code == 200
    db.refresh(book)
    assert book.rating_count == 0
    assert Decimal(book.rating) == Decimal("0.00")


def test_cannot_modify_others_review(client, db, reader_headers):
    book = _book(db)
    admin_headers = auth_headers(client, "admin")
    review_id = client.post(f"/api/books/{book.id}/reviews", headers=admin_headers,
                           json={"rating": 5}).json()["id"]

    assert client.put(f"/api/reviews/{review_id}", headers=reader_headers,
                      json={"rating": 1}).status_code == 403
    assert client.delete(f"/api/reviews/{review_id}", headers=reader_headers).status_code == 403


def test_librarian_hide_review_recomputes_rating(client, db, librarian_headers):
    book = _book(db)
    admin_headers = auth_headers(client, "admin")
    student_headers = auth_headers(client, "student")
    client.post(f"/api/books/{book.id}/reviews", headers=admin_headers, json={"rating": 5})
    bad = client.post(f"/api/books/{book.id}/reviews", headers=student_headers,
                      json={"rating": 1, "content": "违规内容"}).json()["id"]

    hidden = client.put(f"/api/reviews/{bad}/visibility", headers=librarian_headers, json={"is_hidden": True})
    assert hidden.status_code == 200

    db.refresh(book)
    assert book.rating_count == 1
    assert Decimal(book.rating) == Decimal("5.00")

    # 普通读者看不到被隐藏的书评
    visible = client.get(f"/api/books/{book.id}/reviews", headers=student_headers).json()
    assert bad not in [r["id"] for r in visible]

    # 馆员可通过管理列表看到被隐藏书评
    moderation = client.get("/api/reviews", headers=librarian_headers, params={"visible": False}).json()
    assert bad in [r["id"] for r in moderation]


def test_recommendations_respect_history_and_limit(client, db):
    student = db.query(User).filter(User.username == "student").first()
    headers = auth_headers(client, "student")

    borrowed_ids = {b for (b,) in db.query(BorrowRecord.book_id).filter(BorrowRecord.user_id == student.id).all()}
    items = client.get("/api/recommendations", headers=headers, params={"limit": 5}).json()

    assert 0 < len(items) <= 5
    assert all(item["reason"] for item in items)
    assert not ({item["book"]["id"] for item in items} & borrowed_ids), "已借过的书不应再推荐"


def test_recommendations_fallback_for_new_reader(client):
    """无借阅历史的新读者也能拿到兜底推荐（管理员账号无借阅记录）"""
    items = client.get("/api/recommendations", headers=auth_headers(client, "admin"),
                       params={"limit": 3}).json()
    assert len(items) == 3


def test_similar_books_exclude_self(client, db):
    book = _book(db)
    items = client.get(f"/api/books/{book.id}/similar", headers=auth_headers(client, "admin"),
                       params={"limit": 4}).json()
    assert items
    assert book.id not in [i["book"]["id"] for i in items]