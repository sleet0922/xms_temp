@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "VENV=%~dp0.venv"
set "PY=%VENV%\Scripts\python.exe"
set "PIP_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"
set "APP_URL=http://127.0.0.1:8000"

echo ==========================================
echo   智慧图书馆管理系统 - 一键本地编译运行
echo   依赖仅写入项目目录 [.venv / node_modules]
echo   不改动系统 Python 与全局 npm 环境
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 goto no_python
where node >nul 2>nul
if errorlevel 1 goto no_node

if exist "%PY%" goto venv_ready
echo [1/5] 创建本地虚拟环境 .venv
call python -m venv "%VENV%"
if errorlevel 1 goto venv_fail
goto install_backend

:venv_ready
echo [1/5] 复用本地虚拟环境 .venv

:install_backend
echo [2/5] 安装后端依赖到 .venv
"%PY%" -m pip install --disable-pip-version-check -q -i %PIP_MIRROR% -r backend\requirements.txt
set "RC=%errorlevel%"
if not "%RC%"=="0" "%PY%" -m pip install --disable-pip-version-check -q -r backend\requirements.txt
set "RC=%errorlevel%"
if not "%RC%"=="0" goto backend_fail

if exist "frontend\node_modules" goto npm_ready
echo [3/5] 安装前端依赖到 frontend\node_modules
pushd frontend
call npm install --no-audit --no-fund
set "RC=%errorlevel%"
popd
if not "%RC%"=="0" goto npm_fail
goto build_frontend

:npm_ready
echo [3/5] 复用 frontend\node_modules

:build_frontend
echo [4/5] 编译前端静态资源到 frontend\dist
pushd frontend
call npm run build
set "RC=%errorlevel%"
popd
if not "%RC%"=="0" goto build_fail

echo [5/5] 初始化 SQLite 数据库 backend\library.db
pushd backend
"%PY%" init_db.py
set "RC=%errorlevel%"
popd
if not "%RC%"=="0" goto db_fail

echo.
echo 服务启动中，浏览器将自动打开 %APP_URL% ，按 Ctrl+C 可停止服务
echo 默认账号: admin    初始密码: admin123
echo.
start "" /min cmd /c "timeout /t 3 >nul & start %APP_URL%"
pushd backend
"%PY%" -m uvicorn app:app --host 127.0.0.1 --port 8000
popd

echo.
echo 服务已停止，数据保存在 backend\library.db
pause
exit /b 0

:no_python
echo [错误] 未检测到 python，请先安装 Python 3.10+ 并加入 PATH
goto fail

:no_node
echo [错误] 未检测到 node/npm，请先安装 Node.js 18+ 并加入 PATH
goto fail

:venv_fail
echo [错误] 虚拟环境创建失败
goto fail

:backend_fail
echo [错误] 后端依赖安装失败
goto fail

:npm_fail
echo [错误] 前端依赖安装失败
goto fail

:build_fail
echo [错误] 前端编译失败
goto fail

:db_fail
echo [错误] 数据库初始化失败
goto fail

:fail
echo.
pause
exit /b 1