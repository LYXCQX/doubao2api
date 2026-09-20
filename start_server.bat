@echo off
chcp 65001 >nul
title Doubao 2API - 启动服务
cd /d "%~dp0"

echo ========================================================
echo   Doubao 2API - OpenAI 兼容代理服务
echo ========================================================
echo.

:: 1. 检查 Python 环境
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+ 并勾选 "Add to PATH"！
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. 检查并初始化虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [提示] 首次运行，正在自动调用 install.bat 初始化运行环境...
    call install.bat
    if not exist ".venv\Scripts\activate.bat" (
        echo [错误] 环境初始化未完成，请排查后重试。
        pause
        exit /b 1
    )
)

:: 3. 激活虚拟环境
call .venv\Scripts\activate.bat

:: 4. 启动服务（内置端口检测与控制台自动打开）
python -m doubao2api

if %errorlevel% neq 0 (
    echo.
    echo [提示] 服务已退出。若遇异常，可尝试运行 repair.bat 修复残留进程。
    pause
)
