@echo off
rem Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem Create and activate Python virtual environment
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    
    rem Activate virtual environment (batch style)
    call .venv\Scripts\activate.bat
    
    rem Install dependencies
    pip install -r requirements.txt
) else (
    rem Activate virtual environment (batch style)
    call .venv\Scripts\activate.bat
)

rem Start the Flask server for authentication
flask --app src/main run 