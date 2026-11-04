@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo SERS is not installed. Run setup_windows.bat first.
  pause
  exit /b 1
)
call venv\Scripts\activate.bat
python manage.py runserver 127.0.0.1:8000
pause
