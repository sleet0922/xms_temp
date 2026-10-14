#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

command -v node >/dev/null 2>&1 || { echo "[错误] 未找到 Node.js 18+。" >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "[错误] 未找到 npm。" >&2; exit 1; }

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "[1/2] 安装前端依赖…"
  (cd "$FRONTEND_DIR" && npm ci --no-audit --no-fund)
else
  echo "[1/2] 复用 frontend/node_modules"
fi

echo "[2/2] 构建 Vue 前端…"
(cd "$FRONTEND_DIR" && npm run build)
echo "Vue 构建完成：$FRONTEND_DIR/dist"
