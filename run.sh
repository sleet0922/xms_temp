#!/usr/bin/env bash
set -e

# 获取脚本所在目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

VENV="$PROJECT_ROOT/.venv"
PIP_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
APP_URL="http://127.0.0.1:8000"

echo "=========================================="
echo "  智慧图书馆管理系统 - 一键本地编译运行"
echo "  依赖仅写入项目目录 [.venv / node_modules]"
echo "  不改动系统 Python 与全局 npm 环境"
echo "=========================================="
echo ""

# 1. 依赖检测
command -v python3 >/dev/null 2>&1 || { echo "[错误] 未检测到 python3，请先安装 Python 3.10+ 并加入 PATH"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "[错误] 未检测到 node，请先安装 Node.js 18+ 并加入 PATH"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "[错误] 未检测到 npm，请先安装 npm"; exit 1; }

# 2. 虚拟环境创建/复用
if [ ! -d "$VENV" ]; then
    echo "[1/5] 创建本地虚拟环境 .venv..."
    python3 -m venv "$VENV"
else
    echo "[1/5] 复用本地虚拟环境 .venv"
fi
source "$VENV/bin/activate"

# 3. 后端依赖安装
echo "[2/5] 安装后端依赖到 .venv..."
pip install --disable-pip-version-check -q -i "$PIP_MIRROR" -r backend/requirements.txt || \
pip install --disable-pip-version-check -q -r backend/requirements.txt

# 4. 前端依赖安装与构建
if [ ! -d "frontend/node_modules" ]; then
    echo "[3/5] 安装前端依赖到 frontend/node_modules..."
    (cd frontend && npm install --no-audit --no-fund)
else
    echo "[3/5] 复用 frontend/node_modules"
fi

echo "[4/5] 编译前端静态资源到 frontend/dist..."
(cd frontend && npm run build)

# 5. 数据库初始化
echo "[5/5] 初始化 SQLite 数据库 backend/library.db..."
(cd backend && python init_db.py)

echo ""
echo "=========================================="
echo "服务启动成功！"
echo "访问地址: $APP_URL"
echo "API 文档: $APP_URL/docs"
echo "默认账号: admin    初始密码: admin123"
echo "按 Ctrl+C 可停止服务"
echo "=========================================="
echo ""

# 尝试在桌面环境中自动打开浏览器
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    if command -v xdg-open >/dev/null 2>&1; then
        (sleep 2 && xdg-open "$APP_URL") >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        (sleep 2 && open "$APP_URL") >/dev/null 2>&1 &
    fi
fi

cd backend
exec uvicorn app:app --host 127.0.0.1 --port 8000
