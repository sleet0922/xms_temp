#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [[ -x "$VENV_PYTHON" ]]; then
  PYTHON="$VENV_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
else
  echo "[错误] 未找到 Python 3.10+，或项目虚拟环境 .venv 不存在。" >&2
  exit 1
fi

[[ -d "$ROOT_DIR/frontend/dist" ]] || {
  echo "[错误] frontend/dist 不存在，请先运行 ./vue-build.sh。" >&2
  exit 1
}

cd "$BACKEND_DIR"
exec "$PYTHON" -m uvicorn app:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}"
