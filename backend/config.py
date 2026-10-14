"""集中配置层：环境变量 / backend/.env 优先，代码内只保留安全的开发默认值。

生产部署时通过环境变量覆盖即可，无需改代码，例如：
    DATABASE_URL=mysql+pymysql://user:pwd@host/lib
    SECRET_KEY=<随机长串>
"""
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- 应用元信息 ---
    app_name: str = "未来智慧图书馆管理系统 API"
    app_version: str = "3.0.0"
    app_description: str = "支持 RBAC 权限隔离、全流程智慧借还台、条码追踪、逾期罚金、书评推荐与数据可视化的企业级图书管理系统"
    library_name: str = "未来智慧云图书馆"  # 系统设置 library_name 缺失时的兜底显示名

    # --- 数据库 ---
    database_url: str = ""  # 留空则使用 backend/library.db

    # --- 安全 / JWT ---
    secret_key: str = "future-library-jwt-secret-key-production-ready-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 天

    # --- CORS ---
    cors_origins: List[str] = ["*"]

    # --- 业务规则默认值（可被系统设置表中的同名键覆盖）---
    default_borrow_days: int = 30
    max_renew_times: int = 2
    renew_days: int = 15
    daily_fine_rate: Decimal = Decimal("0.50")
    reservation_expire_days: int = 7
    max_borrow_books: int = 8
    due_reminder_days: int = 3  # 借阅到期前几日生成提醒

    # --- 路径 ---
    frontend_dist: str = ""
    covers_dir: str = ""
    resources_dir: str = ""

    def model_post_init(self, __context) -> None:
        if not self.database_url:
            self.database_url = f"sqlite:///{BASE_DIR / 'library.db'}"
        if not self.frontend_dist:
            self.frontend_dist = str(PROJECT_ROOT / "frontend" / "dist")
        if not self.covers_dir:
            self.covers_dir = str(BASE_DIR / "static" / "covers")
        if not self.resources_dir:
            self.resources_dir = str(PROJECT_ROOT / "resources")


settings = Settings()

# 兼容旧模块的导入方式
DATABASE_URL = settings.database_url
IS_SQLITE = DATABASE_URL.startswith("sqlite")