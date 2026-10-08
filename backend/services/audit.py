"""审计日志与系统设置读取：供各路由复用的基础服务"""
import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from config import settings
from models import AuditLog, SystemSetting, User

logger = logging.getLogger("library-api")


def record_audit(
    db: Session,
    user: Optional[User],
    action: str,
    target_type: str,
    target_id: str,
    detail: str,
    request: Optional[Request] = None,
):
    """写入一条审计日志（失败不影响主流程）"""
    try:
        ip = request.client.host if request and request.client else "127.0.0.1"
        log = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else "anonymous",
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            detail=detail,
            ip_address=ip,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"审计日志写入失败: {e}")


def get_setting_val(db: Session, key: str, default: str) -> str:
    s = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
    return s.setting_value if s else default


def get_setting_int(db: Session, key: str, default: int) -> int:
    raw = (get_setting_val(db, key, str(default)) or "").strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def get_setting_decimal(db: Session, key: str, default: Decimal) -> Decimal:
    raw = (get_setting_val(db, key, str(default)) or "").strip()
    try:
        value = Decimal(raw)
        return value if value.is_finite() else default
    except (InvalidOperation, TypeError, ValueError):
        return default


def get_rules(db: Session) -> dict:
    """一次性取出全部业务规则，避免路由中重复查询"""
    borrow_days = get_setting_int(db, "default_borrow_days", settings.default_borrow_days)
    max_renew_times = get_setting_int(db, "max_renew_times", settings.max_renew_times)
    renew_days = get_setting_int(db, "renew_days", settings.renew_days)
    fine_rate = get_setting_decimal(db, "daily_fine_rate", settings.daily_fine_rate)
    max_borrow_books = get_setting_int(db, "max_borrow_books", settings.max_borrow_books)
    reservation_expire_days = get_setting_int(
        db, "reservation_expire_days", settings.reservation_expire_days
    )
    due_reminder_days = get_setting_int(db, "due_reminder_days", settings.due_reminder_days)
    return {
        "borrow_days": max(1, borrow_days),
        "max_renew_times": max(0, max_renew_times),
        "renew_days": max(1, renew_days),
        "fine_rate": max(Decimal("0.00"), fine_rate),
        "max_borrow_books": max(1, max_borrow_books),
        "reservation_expire_days": max(1, reservation_expire_days),
        "due_reminder_days": max(0, due_reminder_days),
    }
