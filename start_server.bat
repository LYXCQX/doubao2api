@echo off
chcp 65001 >nul
title 豆包 2API 启动程序
cd /d "%~dp0"

echo ===================================================================
echo   Doubao 2API - OpenAI 兼容反向代理服务
echo   本地服务:      http://127.0.0.1:9090
echo   管理控制台:    http://127.0.0.1:9090/admin
echo   OpenAI API:   http://127.0.0.1:9090/v1
echo   核心特性:     🔥 即用即焚模式 (请求完成后自动清理豆包临时对话)
echo   注意事项:     若弹出豆包浏览器窗口，请勿手动关闭（为后台驱动引擎）
echo ===================================================================
echo.

rem 寻找可用 Python 解释器
set "PY_EXE="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_EXE=python"
    )
)

if "%PY_EXE%"=="" (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并将其添加到系统 PATH 环境变量。
    echo 官网下载: https://www.python.org/downloads/
    pause
    exit /b 1
)

rem 检查核心依赖是否存在
"%PY_EXE%" -c "import fastapi, playwright, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 首次运行检测到缺少运行依赖，正在自动安装...
    "%PY_EXE%" -m pip install -r "%~dp0requirements.txt"
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请检查网络后重试。
        pause
        exit /b 1
    )
    echo [提示] 正在安装 Playwright 浏览器内核 (Chromium)...
    "%PY_EXE%" -m playwright install chromium
)

rem 检查 9090 端口是否已被旧进程占用，如有则自动释放
netstat -ano | findstr ":9090.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo [提示] 检测到旧服务进程仍在占用 9090 端口，正在自动释放并重启...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9090.*LISTENING"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 1 /nobreak >nul
)

echo [提示] 正在启动服务...
echo [提示] 启动成功后将在 3 秒内自动在默认浏览器中打开管理后台页面...
echo.

set DOUBAO_HEADLESS=auto
set DOUBAO_AUTO_OPEN=true
set DOUBAO_AUTO_DELETE_CONV=true

start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:9090/admin"

"%PY_EXE%" -m doubao2api

pause
