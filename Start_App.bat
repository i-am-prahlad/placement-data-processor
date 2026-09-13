@echo off
title Student Placement Data Processor
cd /d "%~dp0"

:: If run from the root directory, navigate into placement_data_processor
if exist "placement_data_processor\app.py" (
    cd /d "%~dp0placement_data_processor"
)

echo ===================================================
echo     Student Placement Data Processor
echo ===================================================
echo Starting application...
echo The app will open in your browser shortly (http://localhost:8501).
echo Close this window or press Ctrl+C to stop the application.
echo.

:: Check for virtual environment first, otherwise fallback to system python
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" -m streamlit run app.py
) else (
    python -m streamlit run app.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] An error occurred while starting the application.
    echo Please ensure Python and required packages are installed:
    echo     pip install -r requirements.txt
    echo.
    pause
)
