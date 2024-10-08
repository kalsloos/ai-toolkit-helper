@echo off
REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run main.py and capture its exit code
python main.py
set PYTHON_EXIT_CODE=%ERRORLEVEL%

REM Deactivate the virtual environment
call venv\Scripts\deactivate.bat

REM Check if there was an error
if %PYTHON_EXIT_CODE% neq 0 (
    echo.
    echo An error occurred while running the script.
    echo Error code: %PYTHON_EXIT_CODE%
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo.
    echo Script completed successfully.
    echo.
    echo Press any key to exit...
    pause >nul
)