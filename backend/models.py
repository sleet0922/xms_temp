from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(50), unique=True, nullable=False, index=True)
    setting_value = Column(String(255), nullable=False)
    description = Column(String(200))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(255))
    icon = Column(String(50), default="mdi-folder")
    created_at = Column(DateTime, default=datetime.now)

    books = relationship("Book", back_populates="category")

class ShelfLocation(Base):
    __tablename__ = "shelf_locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(30), unique=True, nullable=False, index=True)
    floor = Column(String(20), nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

    books = relationship("Book", back_populates="location")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="reader", nullable=False, index=True)  # admin, librarian, reader
    card_number = Column(String(30), unique=True, nullable=False, index=True)
    max_borrow_limit = Column(Integer, default=5, nullable=False)
    balance = Column(Numeric(10, 2), default=0.00, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, frozen
    created_at = Column(DateTime, default=datetime.now)

    borrow_records = relationship("BorrowRecord", foreign_keys="BorrowRecord.user_id", back_populates="user")
    reservations = relationship("Reservation", back_populates="user")
    fine_records = relationship("FineRecord", back_populates="user")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    isbn = Column(String(20), unique=True, index=True, nullable=True)  # 电子资源可能缺 ISBN
    publisher = Column(String(100))
    publish_date = Column(String(20))
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("shelf_locations.id", ondelete="SET NULL"), nullable=True, index=True)
    price = Column(Numeric(8, 2), default=0.00)
    description = Column(Text)
    cover_url = Column(String(500))
    cover_file = Column(String(200))  # 本地封面文件名（resources/covers 或静态目录）
    tags = Column(String(255))

    # --- 电子资源属性（来自外部数据源，用于详情页增强）---
    language = Column(String(20), index=True)
    format = Column(String(20), index=True)  # pdf / epub / mobi / azw3 / txt ...
    pages = Column(Integer)
    file_size = Column(String(30))
    toc = Column(Text)  # 目录
    author_bio = Column(Text)  # 作者简介
    source_url = Column(String(500))  # 来源页面链接
    source_views = Column(Integer, default=0)
    source_likes = Column(Integer, default=0)
    source_comments = Column(Integer, default=0)

    # --- 馆内聚合指标 ---
    rating = Column(Numeric(3, 2), default=0)  # 书评平均分 0.00 ~ 5.00
    rating_count = Column(Integer, default=0)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    borrow_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    category = relationship("Category", back_populates="books")
    location = relationship("ShelfLocation", back_populates="books")
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")
    borrow_records = relationship("BorrowRecord", back_populates="book")
    reservations = relationship("Reservation", back_populates="book")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

class BookCopy(Base):
    __tablename__ = "book_copies"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    barcode = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="available", nullable=False, index=True) # available, borrowed, reserved, maintenance, lost
    condition_status = Column(String(20), default="good") # good, minor_damage, damaged
    location_note = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)

    book = relationship("Book", back_populates="copies")
    borrow_records = relationship("BorrowRecord", back_populates="copy")

class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    copy_id = Column(Integer, ForeignKey("book_copies.id", ondelete="SET NULL"), nullable=True)
    borrow_date = Column(DateTime, default=datetime.now, nullable=False)
    due_date = Column(DateTime, nullable=False, index=True)
    return_date = Column(DateTime, nullable=True)
    renew_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="borrowed", nullable=False, index=True) # borrowed, returned, overdue, lost
    return_request_status = Column(String(20), default="none", nullable=False, index=True) # none, pending, approved, rejected
    return_requested_at = Column(DateTime, nullable=True)
    librarian_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", foreign_keys=[user_id], back_populates="borrow_records")
    book = relationship("Book", back_populates="borrow_records")
    copy = relationship("BookCopy", back_populates="borrow_records")
    librarian = relationship("User", foreign_keys=[librarian_id])
    fine_records = relationship("FineRecord", back_populates="borrow_record")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    reserve_date = Column(DateTime, default=datetime.now, nullable=False)
    expire_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="waiting", nullable=False, index=True) # waiting, notified, fulfilled, cancelled
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="reservations")
    book = relationship("Book", back_populates="reservations")

class FineRecord(Base):
    __tablename__ = "fine_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    borrow_id = Column(Integer, ForeignKey("borrow_records.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(8, 2), nullable=False)
    reason = Column(String(50), default="overdue", nullable=False) # overdue, damage, lost
    status = Column(String(20), default="unpaid", nullable=False, index=True) # unpaid, paid, waived
    paid_at = Column(DateTime, nullable=True)
    notes = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="fine_records")
    borrow_record = relationship("BorrowRecord", back_populates="fine_records")

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String(20), default="normal", nullable=False) # normal, important, urgent
    is_active = Column(Boolean, default=True, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    author = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(50))
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50))
    target_id = Column(String(50))
    detail = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)


class Review(Base):
    """读者书评与评分（每位读者对同一本书只保留一条，可修改）"""
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_review_user_book"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1 ~ 5 星
    content = Column(Text)
    is_hidden = Column(Boolean, default=False, nullable=False)  # 馆员可隐藏违规书评
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User")
    book = relationship("Book", back_populates="reviews")


class Notification(Base):
    """站内通知：预约到书、到期提醒、罚金产生等"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(30), default="system", nullable=False, index=True)  # reservation_ready / due_reminder / overdue / fine / system
    title = Column(String(150), nullable=False)
    content = Column(Text)
    link = Column(String(200))  # 前端跳转路径
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
