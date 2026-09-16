from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# --- 系统设置 ---
class SettingUpdate(BaseModel):
    setting_value: str

class SettingResponse(BaseModel):
    id: int
    setting_key: str
    setting_value: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 分类与书架 ---
class CategoryBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    icon: Optional[str] = "mdi-folder"

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: Optional[datetime] = None
    book_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ShelfLocationBase(BaseModel):
    name: str
    code: str
    floor: str
    description: Optional[str] = None

class ShelfLocationCreate(ShelfLocationBase):
    pass

class ShelfLocationResponse(ShelfLocationBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 用户与鉴权 ---
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: Optional[str] = "reader"
    card_number: Optional[str] = None
    max_borrow_limit: Optional[int] = 5
    balance: Optional[Decimal] = Decimal("0.00")
    status: Optional[str] = "active"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    max_borrow_limit: Optional[int] = None
    status: Optional[str] = None
    balance: Optional[Decimal] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# --- 图书单册实体 ---
class BookCopyBase(BaseModel):
    barcode: str
    status: Optional[str] = "available"
    condition_status: Optional[str] = "good"
    location_note: Optional[str] = None

class BookCopyCreate(BookCopyBase):
    book_id: int

class BookCopyResponse(BookCopyBase):
    id: int
    book_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 图书主表 ---
class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    publisher: Optional[str] = None
    publish_date: Optional[str] = None
    category_id: Optional[int] = None
    location_id: Optional[int] = None
    price: Optional[Decimal] = Decimal("0.00")
    description: Optional[str] = None
    cover_url: Optional[str] = None
    tags: Optional[str] = None
    total_copies: Optional[int] = 1

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[str] = None
    category_id: Optional[int] = None
    location_id: Optional[int] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    tags: Optional[str] = None

class BookResponse(BookBase):
    id: int
    available_copies: int
    borrow_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    category: Optional[CategoryResponse] = None
    location: Optional[ShelfLocationResponse] = None
    copies: Optional[List[BookCopyResponse]] = []

    class Config:
        from_attributes = True

# --- 借还流通 ---
class BorrowRecordCreate(BaseModel):
    book_id: int
    copy_barcode: Optional[str] = None

class QuickCirculationBorrow(BaseModel):
    card_number: str
    barcode: str

class QuickCirculationReturn(BaseModel):
    barcode: Optional[str] = None
    record_id: Optional[int] = None

class BorrowRecordResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    copy_id: Optional[int] = None
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    renew_count: int
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    book: Optional[BookResponse] = None
    copy: Optional[BookCopyResponse] = None
    overdue_days: Optional[int] = 0
    calculated_fine: Optional[Decimal] = Decimal("0.00")

    class Config:
        from_attributes = True

# --- 预约 ---
class ReservationCreate(BaseModel):
    book_id: int

class ReservationResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    reserve_date: datetime
    expire_date: datetime
    status: str
    created_at: Optional[datetime] = None
    book: Optional[BookResponse] = None
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# --- 罚金账单 ---
class FinePayRequest(BaseModel):
    waive: Optional[bool] = False
    notes: Optional[str] = None

class FineRecordResponse(BaseModel):
    id: int
    user_id: int
    borrow_id: Optional[int] = None
    amount: Decimal
    reason: str
    status: str
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# --- 公告 ---
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    priority: Optional[str] = "normal"
    is_active: Optional[bool] = True

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    priority: str
    is_active: bool
    author_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 审计日志 ---
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 统计报表概览 ---
class StatsOverview(BaseModel):
    total_books: int
    total_copies: int
    total_readers: int
    active_borrows: int
    overdue_borrows: int
    today_borrows: int
    today_returns: int
    unpaid_fines: Decimal
    user_borrowed: Optional[int] = 0
    user_overdue: Optional[int] = 0
    user_fines: Optional[Decimal] = Decimal("0.00")
