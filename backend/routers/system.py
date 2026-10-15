"""全局系统设置、审计日志与运行信息（管理员）"""
from typing import List

from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from auth import require_admin
from config import settings
from database import get_db
from models import AuditLog, SystemSetting, User
from schemas import AuditLogResponse, SettingResponse, SettingUpdate
from services.audit import get_rules, get_setting_val, record_audit

router = APIRouter(tags=["系统管理"])

# 错误提示面向管理员，使用与设置页一致的中文名称，不暴露内部键名
SETTING_LABELS = {
    "library_name": "图书馆名称",
    "default_borrow_days": "借期天数",
    "max_renew_times": "最大续借次数",
    "renew_days": "续借天数",
    "daily_fine_rate": "日罚金",
    "max_borrow_books": "借阅上限",
    "reservation_expire_days": "预约保留天数",
    "due_reminder_days": "到期提醒提前天数",
}


@router.get("/api/system/config", summary="公开系统配置（馆名与业务规则，无需登录）")
def public_system_config(db: Session = Depends(get_db)):
    """前端品牌名与业务规则提示统一从这里读取，避免各处写死。"""
    rules = get_rules(db)
    return {
        "library_name": get_setting_val(db, "library_name", settings.library_name),
        "rules": {
            "borrow_days": rules["borrow_days"],
            "max_renew_times": rules["max_renew_times"],
            "renew_days": rules["renew_days"],
            "daily_fine_rate": str(rules["fine_rate"]),
            "max_borrow_books": rules["max_borrow_books"],
            "reservation_expire_days": rules["reservation_expire_days"],
            "due_reminder_days": rules["due_reminder_days"],
        },
    }


@router.get("/api/settings", response_model=List[SettingResponse], summary="系统设置列表")
def get_system_settings(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return db.query(SystemSetting).all()


@router.put("/api/settings/{setting_key}", response_model=SettingResponse, summary="更新系统设置")
def update_system_setting(
    setting_key: str,
    val_in: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    numeric_rules = {
        "default_borrow_days": (int, 1),
        "max_renew_times": (int, 0),
        "renew_days": (int, 1),
        "daily_fine_rate": (Decimal, 0),
        "max_borrow_books": (int, 1),
        "reservation_expire_days": (int, 1),
        "due_reminder_days": (int, 0),
    }
    if setting_key in numeric_rules:
        converter, minimum = numeric_rules[setting_key]
        label = SETTING_LABELS.get(setting_key, "该设置")
        try:
            parsed = converter(val_in.setting_value.strip())
        except (TypeError, ValueError, InvalidOperation):
            hint = "整数" if converter is int else "数字"
            raise HTTPException(status_code=400, detail=f"「{label}」必须是有效{hint}")
        if isinstance(parsed, Decimal) and not parsed.is_finite():
            raise HTTPException(status_code=400, detail=f"「{label}」必须是有限数字")
        if parsed < minimum:
            raise HTTPException(status_code=400, detail=f"「{label}」不能小于 {minimum}")

    s = db.query(SystemSetting).filter(SystemSetting.setting_key == setting_key).first()
    if not s:
        s = SystemSetting(setting_key=setting_key, setting_value=val_in.setting_value, description="自定义设置")
        db.add(s)
    else:
        s.setting_value = val_in.setting_value

    # 「普通读者最大借阅本数」：借阅限额校验读的是每读者字段，
    # 因此改全局设置时同步下发到现有普通读者，保证设置立即生效且档案显示一致。
    if setting_key == "max_borrow_books":
        db.query(User).filter(User.role == "reader").update(
            {User.max_borrow_limit: int(parsed)}, synchronize_session=False
        )

    db.commit()
    db.refresh(s)
    record_audit(db, current_user, "UPDATE_SETTING", "SETTINGS", setting_key,
                 f"更新规则 {setting_key}={val_in.setting_value}")
    return s


@router.get("/api/audit-logs", response_model=List[AuditLogResponse], summary="审计日志")
def get_audit_logs(
    action: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


@router.get("/api/system/info", summary="系统运行信息")
def system_info(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    rules = get_rules(db)
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "database": "SQLite" if settings.database_url.startswith("sqlite") else "MySQL",
        "covers_dir": settings.covers_dir,
        "rules": {
            "default_borrow_days": rules["borrow_days"],
            "max_renew_times": rules["max_renew_times"],
            "renew_days": rules["renew_days"],
            "daily_fine_rate": str(rules["fine_rate"]),
            "max_borrow_books": rules["max_borrow_books"],
            "reservation_expire_days": rules["reservation_expire_days"],
            "due_reminder_days": rules["due_reminder_days"],
        },
        "token_expire_minutes": settings.access_token_expire_minutes,
    }
