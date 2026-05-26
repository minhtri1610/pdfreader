#!/bin/bash
# packaging script for Kailash PDF Reader

# Exit immediately if a command exits with a non-zero status
set -e

echo "=========================================================="
echo " Starting Packaging Process for Kailash PDF Reader "
echo "=========================================================="

# 1. Check and activate virtual environment
if [ -d ".venv" ]; then
    echo "--> Activating virtual environment..."
    source .venv/bin/activate
else
    echo "--> Error: .venv virtual environment not found!"
    exit 1
fi

# 2. Upgrade pip, install PyInstaller and Pillow (for icon conversion)
echo "--> Checking and installing PyInstaller and Pillow..."
pip install --upgrade pip
pip install pyinstaller Pillow

# 3. Clean previous builds if any
echo "--> Cleaning up old build folders..."
rm -rf build dist KailashPDFReader.spec PremiumPDFReader.spec

# 4. Packaging the app using PyInstaller
echo "--> Bundling the application with PyInstaller..."
# --windowed / --noconsole: Create a windowed app bundle (macOS .app / Windows .exe) without console window
# --onefile: Pack everything into a single executable file/bundle
# --icon: Icon file to use for the app
pyinstaller --noconsole --onefile --windowed --name="KailashPDFReader" --icon="K.png" main.py

# 5. Create DMG disk image on macOS
if [ "$(uname)" == "Darwin" ]; then
    echo "--> Packaging as DMG disk image for macOS distribution..."
    hdiutil create -volname "KailashPDFReader" -srcfolder dist/KailashPDFReader.app -ov -format UDZO dist/KailashPDFReader.dmg
    echo "--> DMG created: dist/KailashPDFReader.dmg"
fi

echo "=========================================================="
echo " Packaging completed successfully! "
echo " You can find your standalone executable inside the 'dist/' folder."
echo "=========================================================="
