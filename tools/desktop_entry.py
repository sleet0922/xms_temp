"""PyInstaller 启动入口：把打包后的 Vue 静态资源交给 FastAPI 托管。"""
import os
import sys
import threading
import webbrowser
from pathlib import Path


if getattr(sys, "frozen", False):
    bundle_root = Path(sys._MEIPASS)
    writable_root = Path(sys.executable).resolve().parent
else:
    bundle_root = Path(__file__).resolve().parents[1]
    writable_root = bundle_root

os.environ.setdefault("FRONTEND_DIST", str(bundle_root / "frontend" / "dist"))
os.environ.setdefault("RESOURCES_DIR", str(bundle_root / "resources"))
os.environ.setdefault("COVERS_DIR", str(writable_root / "library-data" / "covers"))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{writable_root / 'library.db'}")

sys.path.insert(0, str(bundle_root / "backend"))

import uvicorn  # noqa: E402
from app import app  # noqa: E402


if __name__ == "__main__":
    url = f"http://{os.getenv('HOST', '127.0.0.1')}:{os.getenv('PORT', '8000')}"
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
