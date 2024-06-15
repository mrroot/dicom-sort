@echo off

REM Set the virtual environment directory name
set VENV_DIR=venv

REM Check if the virtual environment directory already exists
if not exist %VENV_DIR% (
    echo Virtual environment does not exist. Please run install_venv.bat first.
    exit /b 1
)

REM Activate the virtual environment
call %VENV_DIR%\Scripts\activate

REM Check if the activation was successful
if errorlevel 1 (
    echo Failed to activate the virtual environment.
    exit /b 1
)

REM Run the Python script with passed arguments
python dcmsort.py %*

REM Deactivate the virtual environment
deactivate
