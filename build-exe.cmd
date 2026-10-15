@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "OUT=%ROOT%dist-exe"

where node >nul 2>nul || (echo [错误] 构建机需要 Node.js 18+。 & exit /b 1)
where npm >nul 2>nul || (echo [错误] 构建机需要 npm。 & exit /b 1)
where python >nul 2>nul || (echo [错误] 构建机需要 Python 3.10+。 & exit /b 1)

if exist "%PY%" goto python_ready
echo 创建构建虚拟环境…
python -m venv "%ROOT%.venv"
if errorlevel 1 exit /b 1

:python_ready
"%PY%" -c "import fastapi, uvicorn, sqlalchemy, pydantic" >nul 2>nul
if errorlevel 1 (
  echo 安装后端 Python 依赖…
  "%PY%" -m pip install -r "%ROOT%backend\requirements.txt"
  if errorlevel 1 exit /b 1
)

if exist "%ROOT%frontend\node_modules" goto npm_ready
echo 安装 Vue 依赖…
pushd "%ROOT%frontend"
call npm ci --no-audit --no-fund
if errorlevel 1 (popd & exit /b 1)
popd

:npm_ready
echo 构建 Vue 前端…
pushd "%ROOT%frontend"
call npm run build
if errorlevel 1 (popd & exit /b 1)
popd

"%PY%" -m PyInstaller --version >nul 2>nul
if not errorlevel 1 goto pyinstaller_ready
echo 安装 PyInstaller…
"%PY%" -m pip install pyinstaller
if errorlevel 1 exit /b 1

:pyinstaller_ready
if exist "%OUT%" rmdir /s /q "%OUT%"
if exist "%ROOT%build\pyinstaller" rmdir /s /q "%ROOT%build\pyinstaller"
if exist "%ROOT%library-manager.spec" del /q "%ROOT%library-manager.spec"

echo 打包 Windows 应用…
"%PY%" -m PyInstaller --noconfirm --clean --onedir --noconsole --name library-manager ^
  --distpath "%OUT%" --workpath "%ROOT%build\pyinstaller" ^
  --paths "%ROOT%backend" ^
  --add-data "%ROOT%frontend\dist;frontend\dist" ^
  --add-data "%ROOT%resources;resources" ^
  --collect-all uvicorn --collect-all fastapi --collect-all pydantic ^
  --collect-all pydantic_settings --collect-all sqlalchemy ^
  "%ROOT%tools\desktop_entry.py"
if errorlevel 1 exit /b 1

if exist "%ROOT%backend\library.db" copy /y "%ROOT%backend\library.db" "%OUT%\library-manager\library.db" >nul
if exist "%ROOT%backend\static\covers" (
  mkdir "%OUT%\library-manager\library-data\covers" 2>nul
  xcopy "%ROOT%backend\static\covers\*" "%OUT%\library-manager\library-data\covers\" /E /I /Y /Q >nul
)

echo.
echo 完成：%OUT%\library-manager\library-manager.exe
echo 将整个 library-manager 文件夹复制到没有 Python/Node 的 Windows 电脑，双击 exe 即可启动。
endlocal
