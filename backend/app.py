"""应用装配层：中间件、路由注册、静态资源托管（业务逻辑见 routers/ 与 services/）

启动方式（任选其一）：
    python backend/app.py
    cd backend && python -m uvicorn app:app --host 127.0.0.1 --port 8000
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db
from routers import auth, books, circulation, content, fines, readers, stats, system

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("library-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        os.makedirs(settings.covers_dir, exist_ok=True)
        logger.info("数据库连接与数据模型初始化完成")
    except Exception as e:
        logger.warning(f"启动自动初始化跳过: {e}")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # 通配来源不能与凭据模式同时启用；生产环境可在配置中指定明确来源。
    allow_credentials=settings.cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 业务路由（按领域拆分，接口路径与原版完全兼容）---
for _router in (
    auth.router,
    stats.router,
    books.router,
    circulation.router,
    readers.router,
    fines.router,
    content.router,
    system.router,
):
    app.include_router(_router)

# --- 封面图片静态托管：/covers/{filename} ---
os.makedirs(settings.covers_dir, exist_ok=True)
app.mount("/covers", StaticFiles(directory=settings.covers_dir), name="covers")

# --- 前端静态资源托管（打包产物 frontend/dist）---
FRONTEND_DIST = settings.frontend_dist

if os.path.isdir(FRONTEND_DIST):
    _ASSETS_DIR = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(_ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        """SPA 路由回退：非 /api 路径统一返回 index.html"""
        if full_path.startswith("api") or full_path.startswith("covers"):
            raise HTTPException(status_code=404, detail="资源不存在")
        candidate = os.path.realpath(os.path.join(FRONTEND_DIST, full_path))
        if full_path and candidate.startswith(os.path.realpath(FRONTEND_DIST)) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
