@echo off
chcp 65001 >nul
title Doubao 2API - 故障排查与残留自愈
cd /d "%~dp0"

echo ========================================================
echo   Doubao 2API - 故障排查与残留清理向导
echo ========================================================
echo.
echo 正在检测并清理可能残留的僵尸进程与端口占用...

:: 1. 查找并清理占用 9090 端口的进程
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":9090" ^| findstr "LISTENING"') do (
    echo [发现] 正在终止占用 9090 端口的旧进程 (PID: %%a)...
    taskkill /f /pid %%a >nul 2>nul
)

:: 2. 检查是否有游离的 Playwright / Python 启动的浏览器
echo [清理] 正在清理游离的 Chrome/Playwright 测试窗口...
taskkill /f /im "chrome.exe" /fi "WINDOWTITLE eq *doubao*" >nul 2>nul
taskkill /f /im "msedge.exe" /fi "WINDOWTITLE eq *doubao*" >nul 2>nul

:: 3. 清理锁文件
set "DATA_DIR=%USERPROFILE%\.doubao_browser"
if exist "%DATA_DIR%\SingletonLock" (
    echo [清理] 发现残留的浏览器锁文件 SingletonLock，正在清理...
    del /f /q "%DATA_DIR%\SingletonLock" >nul 2>nul
)

echo.
echo ========================================================
echo   [完成] 残留进程与端口占用清理完毕！
echo   现在您可以重新运行 start_server.bat 尝试正常启动。
echo ========================================================
echo.
pause
