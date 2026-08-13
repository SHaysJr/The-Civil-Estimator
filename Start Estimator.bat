@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -m venv .venv
  echo Installing required packages...
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5051'"
.venv\Scripts\python.exe app.py
pause
