@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -m venv .venv
)

echo Installing build dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul
.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller

echo.
echo Building CivilEstimator.exe ...
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --name CivilEstimator ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --add-data "estimator.db;." ^
  app.py

echo.
echo Done. Your executable is at dist\CivilEstimator.exe
echo Copy that one file anywhere and double-click it - it opens your browser
echo automatically at http://127.0.0.1:5052. Its data file (estimator.db)
echo is created next to wherever you put the .exe, so keep it in its own folder.
pause
