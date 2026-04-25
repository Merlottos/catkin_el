@echo off
:: Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Pip is not installed. Please install pip first.
    exit /b 1
)

:: Check if requirements.txt exists
if not exist "requirements.txt" (
    echo requirements.txt not found in the current directory.
    exit /b 1
)

:: Install packages from requirements.txt
echo Installing packages from requirements.txt...
pip install -r requirements.txt

:: Check if the installation was successful
if %errorlevel% neq 0 (
    echo Failed to install some packages.
    exit /b 1
)

echo Packages installed successfully.
pause