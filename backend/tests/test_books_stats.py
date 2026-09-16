"""书目检索、筛选、导出与统计接口测试"""
from models import Book, BookCopy, BorrowRecord


def test_create_book_generates_copies_and_barcodes(client, db, librarian_headers):
    payload = {
        "title": "测试用书目", "author": "测试作者", "isbn": "9780000000001",
        "publisher": "测试出版社", "language": "中文", "format": "EPUB",
        "pages": 320, "description": "用于自动化测试",
    }
    resp = client.post("/api/books", headers=librarian_headers, params={"copies_count": 3}, json=payload)
    assert resp.status_code == 201, resp.text
    book = resp.json()
    assert book["total_copies"] == 3 and book["available_copies"] == 3
    assert len(book["copies"]) == 3
    assert len({c["barcode"] for c in book["copies"]}) == 3

    # 相同 ISBN 再次录入被拒绝
    assert client.post("/api/books", headers=librarian_headers, json=payload).status_code == 400

    # 无 ISBN 的电子资源可重复录入（isbn 允许为空）
    no_isbn = {"title": "无 ISBN 电子书 A", "author": "佚名"}
    assert client.post("/api/books", headers=librarian_headers, json=no_isbn).status_code == 201
    no_isbn["title"] = "无 ISBN 电子书 B"
    assert client.post("/api/books", headers=librarian_headers, json=no_isbn).status_code == 201


def test_update_and_delete_book(client, db, librarian_headers, admin_headers):
    book = db.query(Book).filter(Book.available_copies > 0).first()
    resp = client.put(f"/api/books/{book.id}", headers=librarian_headers, json={"publisher": "新出版社"})
    assert resp.status_code == 200
    assert resp.json()["publisher"] == "新出版社"

    # 有在借记录的书不可注销
    borrowed_book = db.query(Book).join(BorrowRecord, BorrowRecord.book_id == Book.id).filter(
        BorrowRecord.return_date.is_(None)
    ).first()
    assert client.delete(f"/api/books/{borrowed_book.id}", headers=admin_headers).status_code == 400

    # 馆员无权注销，仅管理员可执行
    clean_book = client.post("/api/books", headers=librarian_headers,
                            json={"title": "待注销图书", "author": "佚名"}).json()
    assert client.delete(f"/api/books/{clean_book['id']}", headers=librarian_headers).status_code == 403
    assert client.delete(f"/api/books/{clean_book['id']}", headers=admin_headers).status_code == 204


def test_search_and_filters(client, db, librarian_headers):
    client.post("/api/books", headers=librarian_headers, json={
        "title": "宇宙物理学导论", "author": "卡尔", "language": "英文", "format": "PDF",
    })

    assert any(b["title"] == "宇宙物理学导论" for b in client.get("/api/books", params={"search": "宇宙物理"}).json())
    assert all("卡尔" in b["author"] for b in client.get("/api/books", params={"author": "卡尔"}).json())
    assert all(b["language"] == "英文" for b in client.get("/api/books", params={"language": "英文"}).json())
    assert all(b["format"] == "PDF" for b in client.get("/api/books", params={"format": "PDF"}).json())
    assert all(b["available_copies"] > 0 for b in client.get("/api/books", params={"in_stock_only": True}).json())

    rated = client.get("/api/books", params={"sort_by": "rating"}).json()
    assert len(rated) > 1


def test_facets_and_csv_export(client, db, librarian_headers):
    facets = client.get("/api/books/facets").json()
    assert facets["total"] == db.query(Book).count()
    assert isinstance(facets["languages"], list) and isinstance(facets["formats"], list)

    client.post("/api/books", headers=librarian_headers,
                json={"title": "带语种的电子书", "author": "佚名", "language": "中文", "format": "EPUB"})
    facets = client.get("/api/books/facets").json()
    assert {"value": "中文", "count": 1} in facets["languages"]
    assert {"value": "EPUB", "count": 1} in facets["formats"]

    resp = client.get("/api/books-export")
    assert resp.status_code == 200
    text = resp.content.decode("utf-8-sig")
    assert "书名" in text.splitlines()[0]
    assert len(text.splitlines()) == db.query(Book).count() + 1


def test_add_copy_updates_stock(client, db, librarian_headers):
    book = db.query(Book).first()
    before = book.total_copies
    resp = client.post(f"/api/books/{book.id}/copies", headers=librarian_headers,
                       json={"barcode": "BK-TEST-COPY-001", "book_id": book.id})
    assert resp.status_code == 200
    db.refresh(book)
    assert book.total_copies == before + 1

    assert client.post(f"/api/books/{book.id}/copies", headers=librarian_headers,
                       json={"barcode": "BK-TEST-COPY-001", "book_id": book.id}).status_code == 400


def test_stats_endpoints(client, db, admin_headers):
    overview = client.get("/api/stats/overview", headers=admin_headers).json()
    for key in ["total_books", "total_copies", "total_readers", "active_borrows", "overdue_borrows",
                "today_borrows", "today_returns", "unpaid_fines", "total_reviews", "avg_rating",
                "total_reservations", "unread_notifications"]:
        assert key in overview, f"概览缺少指标 {key}"
    assert overview["total_books"] == db.query(Book).count()

    assert len(client.get("/api/stats/trends", params={"days": 7}).json()) == 7
    assert len(client.get("/api/stats/categories").json()) > 0
    assert len(client.get("/api/stats/popular-books", params={"limit": 3}).json()) == 3
    assert isinstance(client.get("/api/stats/formats").json(), list)
    assert isinstance(client.get("/api/stats/languages").json(), list)

    readers = client.get("/api/stats/active-readers", params={"limit": 3}).json()
    assert readers and "borrow_total" in readers[0]


def test_reader_overview_profile(client, db, librarian_headers):
    from models import User
    reader = db.query(User).filter(User.username == "student").first()
    resp = client.get(f"/api/readers/{reader.id}/overview", headers=librarian_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["username"] == "student"
    assert body["total_borrows"] >= 1
    assert isinstance(body["favorite_categories"], list)

    # 读者无权查看画像
    assert client.get(f"/api/readers/{reader.id}/overview",
                      headers={"Authorization": "Bearer invalid"}).status_code == 401