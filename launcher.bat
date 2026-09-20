@echo off
chcp 65001 >nul
title Doubao 2API - 便捷管理中心
cd /d "%~dp0"

if "%DOUBAO_PORT%"=="" set "DOUBAO_PORT=9090"
set "STARTUP_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Doubao2API.lnk"

:menu
cls
echo ================================================================
echo               Doubao 2API 便捷管理中心
echo ================================================================

:: 1. 检测服务运行状态 (检测 %DOUBAO_PORT% 端口)
set "SERVER_STATUS=[○ 未运行]"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%DOUBAO_PORT%" ^| findstr "LISTENING"') do set "SERVER_STATUS=[● 运行中] 端口 %DOUBAO_PORT% [PID: %%a]"

:: 2. 检测开机自启状态
set "AUTOSTART_STATUS=[未开启]"
if exist "%STARTUP_LNK%" set "AUTOSTART_STATUS=[已开启]"

echo   当前服务状态: %SERVER_STATUS%
echo   开机自启状态: %AUTOSTART_STATUS%
echo ----------------------------------------------------------------
echo   [1] 启动服务 (前台运行，显示实时日志)
echo   [2] 静默启动 (后台运行，无黑框，就绪后自动打开网页)
echo   [3] 停止服务 (停止当前运行中的服务)
echo   [4] 打开管理网页 (http://127.0.0.1:%DOUBAO_PORT%/admin)
echo ----------------------------------------------------------------
echo   [5] 创建桌面快捷方式 (双击桌面图标直接打开此管理中心)
echo   [6] 切换开机自启动 (开启 / 关闭)
echo ----------------------------------------------------------------
echo   [7] 一键故障修复 (深度清理端口占用与残留浏览器)
echo   [8] 检查并更新到最新版本
echo   [0] 退出
echo ================================================================
set "choice="
set /p choice=请输入操作编号 [0-8]: 

if "%choice%"=="1" goto start_foreground
if "%choice%"=="2" goto start_silent
if "%choice%"=="3" goto stop_server
if "%choice%"=="4" goto open_browser
if "%choice%"=="5" goto make_shortcut
if "%choice%"=="6" goto toggle_autostart
if "%choice%"=="7" goto do_repair
if "%choice%"=="8" goto do_update
if "%choice%"=="0" exit /b 0

echo.
echo [错误] 输入无效，请输入 0 到 8 之间的数字。
timeout /t 2 >nul
goto menu

:start_foreground
echo.
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%DOUBAO_PORT%" ^| findstr "LISTENING"') do goto already_running_fg
echo 正在以前台模式启动服务...
call start_server.bat
pause
goto menu

:already_running_fg
echo [提示] 服务已在运行中，无需重复启动！
echo 正在为您打开管理网页...
start http://127.0.0.1:%DOUBAO_PORT%/admin
pause
goto menu

:start_silent
echo.
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%DOUBAO_PORT%" ^| findstr "LISTENING"') do goto already_running_silent
echo [提示] 正在启动后台静默服务...
wscript "%~dp0run_silent.vbs"
echo [成功] 服务已在后台启动！服务就绪后将自动打开管理网页。
timeout /t 3 >nul
goto menu

:already_running_silent
echo [提示] 服务已在运行中！
echo 正在为您打开管理网页...
start http://127.0.0.1:%DOUBAO_PORT%/admin
pause
goto menu

:stop_server
echo.
set "STOPPED=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%DOUBAO_PORT%" ^| findstr "LISTENING"') do (
    echo 正在停止服务 [PID: %%a]...
    taskkill /f /pid %%a >nul 2>nul
    set "STOPPED=1"
)
if "%STOPPED%"=="1" (
    echo [成功] 服务已停止。
) else (
    echo [提示] 当前没有检测到运行中的 Doubao 2API 服务。
)
pause
goto menu

:open_browser
echo.
echo 正在打开管理控制台: http://127.0.0.1:%DOUBAO_PORT%/admin ...
start http://127.0.0.1:%DOUBAO_PORT%/admin
timeout /t 2 >nul
goto menu

:make_shortcut
echo.
echo 正在生成桌面快捷方式...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Doubao 2API 控制台.lnk')); $s.TargetPath = '%~dp0launcher.bat'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Doubao 2API 便捷管理中心'; $s.Save()"
if %errorlevel% equ 0 goto shortcut_ok
echo [失败] 创建快捷方式失败，请检查系统权限。
pause
goto menu

:shortcut_ok
echo [成功] 已在桌面成功创建快捷方式: [Doubao 2API 控制台]！
pause
goto menu

:toggle_autostart
echo.
if exist "%STARTUP_LNK%" goto disable_autostart
goto enable_autostart

:disable_autostart
echo 正在关闭开机自启动...
del /f /q "%STARTUP_LNK%" >nul 2>nul
echo [成功] 已取消开机自启动！
pause
goto menu

:enable_autostart
echo 正在开启开机自启动...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'Doubao2API.lnk')); $s.TargetPath = '%~dp0run_silent.vbs'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Doubao 2API 后台自启动服务'; $s.Save()"
if %errorlevel% equ 0 goto autostart_ok
echo [失败] 设置开机自启失败，请检查系统权限。
pause
goto menu

:autostart_ok
echo [成功] 已开启开机自启动！系统开机后将自动在后台静默运行 Doubao 2API。
pause
goto menu

:do_repair
echo.
call repair.bat
pause
goto menu

:do_update
echo.
call update.bat
pause
goto menu
