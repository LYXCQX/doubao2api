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

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m doubao2api
) else if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" -m doubao2api
) else (
    python -m doubao2api
)

pause
