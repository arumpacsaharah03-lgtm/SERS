@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher was not found. Install Python 3.12 and add it to PATH.
  pause
  exit /b 1
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env. Update its MySQL password before continuing.
  notepad ".env"
  echo Run setup_windows.bat again after saving .env.
  pause
  exit /b 0
)

if not exist "venv\Scripts\python.exe" (
  py -3.12 -m venv venv
  if errorlevel 1 goto :error
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :error
pip install -r requirements.txt
if errorlevel 1 goto :error
python manage.py migrate
if errorlevel 1 goto :error
python manage.py seed_sers
if errorlevel 1 goto :error

echo.
echo SERS setup completed successfully.
echo Next: run "venv\Scripts\python manage.py createsuperuser"
pause
exit /b 0

:error
echo.
echo Setup failed. Review the error above and confirm MySQL is running.
pause
exit /b 1
