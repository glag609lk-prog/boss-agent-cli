@echo off
chcp 65001 >nul
setlocal EnableExtensions
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

if defined BOSS_INSTALL_DIR (
  set "DEST=%BOSS_INSTALL_DIR%"
) else (
  set "DEST=%LOCALAPPDATA%\HRAssistant"
)

echo.
echo 正在安装招聘助手
echo 安装位置：%DEST%
echo 不会改动你电脑里原来的 Python，也不会删除已经保存的登录信息。
echo.

if /I "%HERE%"=="%DEST%" goto :configured

if not exist "%DEST%" mkdir "%DEST%"
if errorlevel 1 goto :mkdir_failed

robocopy "%HERE%\runtime" "%DEST%\runtime" /MIR /NFL /NDL /NJH /NJS /nc /ns /np
if errorlevel 8 goto :copy_failed

copy /Y "%HERE%\boss.cmd" "%DEST%\boss.cmd" >nul
copy /Y "%HERE%\boss_launch.py" "%DEST%\boss_launch.py" >nul
copy /Y "%HERE%\explain_doctor.py" "%DEST%\explain_doctor.py" >nul
copy /Y "%HERE%\add_user_path.ps1" "%DEST%\add_user_path.ps1" >nul
copy /Y "%HERE%\使用说明.txt" "%DEST%\使用说明.txt" >nul
copy /Y "%HERE%\给Agent的说明.md" "%DEST%\给Agent的说明.md" >nul
copy /Y "%HERE%\安装.bat" "%DEST%\安装.bat" >nul

:configured
echo 正在把命令加入当前用户的 PATH。不需要管理员。
powershell -NoProfile -ExecutionPolicy Bypass -File "%DEST%\add_user_path.ps1" -Dir "%DEST%"
if errorlevel 1 (
  echo 没能自动加入 PATH。程序已经复制好，可以先用下面这个文件：
  echo   "%DEST%\boss.cmd"
  echo.
)

echo 正在下载登录用的浏览器内核。这一步需要联网，不会改你自己的 Chrome。
"%DEST%\runtime\python.exe" -m patchright install chromium
if errorlevel 1 (
  echo.
  echo 浏览器内核没有下载成功。招聘助手本身已经装好。
  echo 连上网络后，重新双击一次「安装.bat」，或者在新的命令行窗口执行：
  echo   "%DEST%\runtime\python.exe" -m patchright install chromium
  echo.
)

echo 正在检查这台电脑：
"%DEST%\boss.cmd" --json doctor > "%TEMP%\hr-assistant-doctor.json"
"%DEST%\runtime\python.exe" "%DEST%\explain_doctor.py" "%TEMP%\hr-assistant-doctor.json"
echo.
if not defined BOSS_INSTALL_NONINTERACTIVE (
  echo 按任意键关闭窗口。
  pause >nul
)
exit /b 0

:mkdir_failed
echo 无法创建安装目录。请确认磁盘没有满，然后重新双击「安装.bat」。
exit /b 1

:copy_failed
echo 复制程序文件失败。请关闭正在使用招聘助手的窗口后重试。
exit /b 1
