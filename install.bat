@echo off
chcp 65001 >nul
title Doubao 2API - 环境安装向导
cd /d "%~dp0"

echo ========================================================
echo   Doubao 2API - 自动环境配置与依赖安装
echo ========================================================
echo.

:: 1. 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到系统 Python，请先安装 Python 3.9 或更高版本！
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. 创建虚拟环境
if not exist ".venv" (
    echo [1/3] 正在创建独立虚拟环境 (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败，请检查 Python 权限！
        pause
        exit /b 1
    )
) else (
    echo [1/3] 虚拟环境 (.venv) 已存在。
)

:: 3. 激活虚拟环境并安装依赖
echo [2/3] 正在使用清华源加速安装 Python 依赖库...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
    echo [警告] 清华源安装出现异常，正在尝试官方源重试...
    pip install -r requirements.txt
)

:: 4. 安装 Playwright Chromium 驱动
echo [3/3] 正在安装 Playwright 通用 Chromium 浏览器内核...
python -m playwright install chromium

echo.
echo ========================================================
echo   [成功] 环境配置已全部完成！
echo   现在您可以直接双击运行 start_server.bat 启动服务。
echo ========================================================
echo.
pause
