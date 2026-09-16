"""认证与 RBAC 权限隔离测试"""
from conftest import auth_headers
from models import BorrowRecord, User


def test_login_success_and_me(client):
    headers = auth_headers(client, "admin")
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"
    assert resp.json()["role"] == "admin"


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "bad-pass"})
    assert resp.status_code == 401


def test_frozen_account_cannot_login(client, frozen_reader):
    resp = client.post("/api/auth/login", json={"username": "lisi", "password": "admin123"})
    assert resp.status_code == 403
    assert "冻结" in resp.json()["detail"]


def test_register_and_duplicate_username(client):
    payload = {
        "username": "newbie", "email": "newbie@future-lib.com", "full_name": "新同学",
        "password": "reader123",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 400


def test_change_password_then_login_with_new_one(client, reader_headers):
    resp = client.put("/api/auth/change-password", headers=reader_headers,
                      json={"old_password": "admin123", "new_password": "reader456"})
    assert resp.status_code == 200
    assert client.post("/api/auth/login", json={"username": "student", "password": "reader456"}).status_code == 200
    assert client.post("/api/auth/login", json={"username": "student", "password": "admin123"}).status_code == 401


def test_change_password_rejects_wrong_old_password(client, reader_headers):
    resp = client.put("/api/auth/change-password", headers=reader_headers,
                      json={"old_password": "wrong", "new_password": "abcdef"})
    assert resp.status_code == 400


def test_reader_cannot_touch_management_endpoints(client, reader_headers):
    for method, url in [
        ("get", "/api/readers"),
        ("get", "/api/settings"),
        ("get", "/api/audit-logs"),
        ("get", "/api/reviews"),
        ("post", "/api/books"),
        ("post", "/api/announcements"),
    ]:
        resp = getattr(client, method)(url, headers=reader_headers)
        assert resp.status_code == 403, f"{method} {url} 应被拒绝"


def test_librarian_scope(client, librarian_headers):
    assert client.get("/api/readers", headers=librarian_headers).status_code == 200
    assert client.get("/api/settings", headers=librarian_headers).status_code == 403
    assert client.get("/api/audit-logs", headers=librarian_headers).status_code == 403


def test_reader_only_sees_own_borrows(client, db, reader_headers):
    student = db.query(User).filter(User.username == "student").first()
    records = client.get("/api/borrows", headers=reader_headers).json()
    assert records, "应有借阅记录"
    assert {r["user_id"] for r in records} == {student.id}
    assert db.query(BorrowRecord).count() > len(records), "其他读者记录不应出现"


def test_anonymous_request_rejected(client):
    assert client.get("/api/books").status_code == 200  # 书目检索开放
    assert client.get("/api/borrows").status_code == 401