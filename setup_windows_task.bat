@echo off
cd /d "%~dp0"
echo === Setup Windows Task Scheduler for AI for Nonprofits ===
echo.

set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=C:\Users\merin\AppData\Local\Programs\Python\Python313\python.exe"
set "TASK_NAME=AI for Nonprofits Daily Post"

echo This will create a daily Windows Task that runs the pipeline.
echo.
echo Script: %SCRIPT_DIR%main.py
echo Python: %PYTHON_PATH%
echo Task:   %TASK_NAME%
echo.

SCHTASKS /CREATE /SC DAILY /TN "%TASK_NAME%" /TR "%PYTHON_PATH% %SCRIPT_DIR%main.py" /ST 09:00 /RI 1440 /DU 24:00 /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Task created successfully!
    echo It will run daily at 9:00 AM.
    echo.
    echo To test:  python main.py
    echo To view:  SCHTASKS /QUERY /TN "%TASK_NAME%"
    echo To edit:  SCHTASKS /CHANGE /TN "%TASK_NAME%" /ST HH:MM
    echo To delete: SCHTASKS /DELETE /TN "%TASK_NAME%" /F
) else (
    echo.
    echo Failed to create task. Run as Administrator if needed.
)

pause
