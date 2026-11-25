@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul && (py -3 main.py) || (python main.py)
if errorlevel 1 pause
