"""pytest 全局夹具：每个用例使用独立的临时 SQLite 库 + 演示种子数据，绝不触碰开发库"""
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# 必须在导入 app/config 之前指定测试库：config.py 会读取该环境变量
_TMP_DB = Path(tempfile.gettempdir()) / "xms_test_library.db"
if _TMP_DB.exists():
    _TMP_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import init_db as seed_module  # noqa: E402
from app import app  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402
from models import Book, BookCopy, BorrowRecord, User  # noqa: E402

DEFAULT_PASSWORD = "admin123"


@pytest.fixture(autouse=True)
def db():
    """每个用例重建库表并灌入种子数据，保证用例间互不干扰"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    seed_module.seed(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def auth_headers(client: TestClient, username: str = "admin", password: str = DEFAULT_PASSWORD) -> dict:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    return auth_headers(client, "admin")


@pytest.fixture
def librarian_headers(client):
    return auth_headers(client, "librarian")


@pytest.fixture
def reader_headers(client):
    return auth_headers(client, "student")


@pytest.fixture
def frozen_reader(db):
    """冻结读者：用于验证冻结账户被拒绝借阅/登录"""
    user = db.query(User).filter(User.username == "lisi").first()
    user.status = "frozen"
    db.commit()
    return user


@pytest.fixture
def available_copy(db):
    """取一册在架可借的实体书（含条码与关联书目）"""
    return db.query(BookCopy).filter(BookCopy.status == "available").first()


@pytest.fixture
def overdue_record(db):
    """为 lisi 造一条已逾期未还的借阅记录（lisi 无历史欠费）"""
    user = db.query(User).filter(User.username == "lisi").first()
    book = db.query(Book).filter(Book.title.like("%原则%")).first()
    copy = db.query(BookCopy).filter(BookCopy.book_id == book.id, BookCopy.status == "available").first()
    copy.status = "borrowed"
    book.available_copies -= 1
    record = BorrowRecord(
        user_id=user.id,
        book_id=book.id,
        copy_id=copy.id,
        borrow_date=datetime.now() - timedelta(days=40),
        due_date=datetime.now() - timedelta(days=10),
        renew_count=0,
        status="overdue",
        notes="测试用逾期记录",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record