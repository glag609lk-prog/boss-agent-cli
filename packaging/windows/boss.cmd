@echo off
chcp 65001 >nul
setlocal
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
"%~dp0runtime\python.exe" "%~dp0boss_launch.py" %*
