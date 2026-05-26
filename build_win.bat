@echo off
echo ==========================================================
echo  Starting Packaging Process for Kailash PDF Reader (Windows)
echo ==========================================================

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH!
    pause
    exit /b 1
)

:: 2. Setup virtual environment if not exists
if not exist .venv (
    echo --> Creating virtual environment .venv...
    python -m venv .venv
)

:: 3. Activate virtual environment and install packages
echo --> Activating virtual environment and installing packages...
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller Pillow

:: 4. Clean previous builds
echo --> Cleaning up old build folders...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist KailashPDFReader.spec del /f /q KailashPDFReader.spec
if exist PremiumPDFReader.spec del /f /q PremiumPDFReader.spec

:: 5. Package with PyInstaller
echo --> Bundling the application with PyInstaller...
:: On Windows, PyInstaller will automatically convert K.png to .ico if Pillow is installed
pyinstaller --noconsole --onefile --windowed --name="KailashPDFReader" --icon="K.png" main.py

echo ==========================================================
echo  Packaging completed successfully!
echo  You can find your standalone executable KailashPDFReader.exe inside the 'dist' folder.
echo ==========================================================
pause
