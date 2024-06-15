@echo off

REM Set the virtual environment directory name
set VENV_DIR=venv

REM Check if the virtual environment directory already exists
if exist %VENV_DIR% (
    echo Virtual environment already exists.
) else (
    REM Create the virtual environment
    python -m venv %VENV_DIR%

    REM Check if the virtual environment was created successfully
    if exist %VENV_DIR% (
        echo Virtual environment created successfully.
    ) else (
        echo Failed to create virtual environment.
        exit /b 1
    )
)

REM Activate the virtual environment
call %VENV_DIR%\Scripts\activate

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo requirements.txt not found.
    exit /b 1
)

REM Install the dependencies from requirements.txt
pip install -r requirements.txt

REM Check if the dependencies were installed successfully
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    exit /b 1
) else (
    echo Dependencies installed successfully.
)

REM Keep the window open
pause