#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

"$ROOT_DIR/vue-build.sh"

PYTHON="$ROOT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3 || true)"
fi
[[ -n "$PYTHON" && -x "$PYTHON" ]] || { echo "[错误] 未找到 Python。" >&2; exit 1; }

echo "检查 PyInstaller…"
if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
  "$PYTHON" -m pip install pyinstaller
fi

SEP=":"
case "$(uname -s 2>/dev/null || true)" in
  MINGW*|MSYS*|CYGWIN*) SEP=";" ;;
esac

OUTPUT_DIR="$ROOT_DIR/dist-exe"
rm -rf "$OUTPUT_DIR" "$ROOT_DIR/build/pyinstaller" "$ROOT_DIR/library-manager.spec"

echo "开始打包应用…"
"$PYTHON" -m PyInstaller \
  --noconfirm --clean --onedir --name library-manager \
  --distpath "$OUTPUT_DIR" --workpath "$ROOT_DIR/build/pyinstaller" \
  --paths "$ROOT_DIR/backend" \
  --add-data "frontend/dist${SEP}frontend/dist" \
  --add-data "resources${SEP}resources" \
  --collect-all uvicorn \
  --collect-all fastapi \
  --collect-all pydantic \
  --collect-all pydantic_settings \
  --collect-all sqlalchemy \
  tools/desktop_entry.py

# 保留已有演示库作为首次运行的数据起点；运行时数据库会写在 exe 同目录。
if [[ -f "$ROOT_DIR/backend/library.db" && ! -f "$OUTPUT_DIR/library-manager/library.db" ]]; then
  cp "$ROOT_DIR/backend/library.db" "$OUTPUT_DIR/library-manager/library.db"
fi
if [[ -d "$ROOT_DIR/backend/static/covers" ]]; then
  mkdir -p "$OUTPUT_DIR/library-manager/library-data/covers"
  cp -a "$ROOT_DIR/backend/static/covers/." "$OUTPUT_DIR/library-manager/library-data/covers/"
fi

echo "打包完成：$OUTPUT_DIR/library-manager"
if [[ "$SEP" == ";" ]]; then
  echo "Windows 可执行文件：$OUTPUT_DIR/library-manager/library-manager.exe"
else
  echo "当前平台可执行文件：$OUTPUT_DIR/library-manager/library-manager"
  echo "要生成 .exe，请在 Windows（或 Windows CI）上运行同一个脚本。"
fi
