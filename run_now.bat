@echo off
cd /d "%~dp0"
echo === AI for Nonprofits — Run Now ===
call .venv\Scripts\activate.bat 2>nul || echo [No venv, using system Python]
python main.py
pause
