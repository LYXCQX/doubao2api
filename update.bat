@echo off
chcp 65001 >nul
title Doubao 2API - 一键版本更新
cd /d "%~dp0"

echo ========================================================
echo   Doubao 2API - 自动同步与依赖更新
echo ========================================================
echo.

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 系统未安装 Git，无法自动拉取远程代码。
    echo 请直接从 GitHub 下载最新的 ZIP 包覆盖本地文件。
    pause
    exit /b 1
)

echo [1/2] 正在通过 Git 拉取最新代码...
git pull
if %errorlevel% neq 0 (
    echo [警告] 代码拉取失败，请检查网络或是否有本地修改冲突。
    pause
    exit /b 1
)

if exist ".venv\Scripts\activate.bat" (
    echo [2/2] 正在更新 Python 依赖库...
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo ========================================================
echo   [成功] 代码与依赖已更新至最新版本！
echo ========================================================
echo.
pause
