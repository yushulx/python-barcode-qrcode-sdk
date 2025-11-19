@echo off
REM Barcode Scanner Setup and Test Script for Windows
REM This script helps set up and test the barcode scanner

echo ============================================
echo Barcode Scanner Setup and Test Script
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b 1
)

echo Python is installed:
python --version

echo.
echo ============================================
echo Installing Dependencies
echo ============================================

REM Install required packages
echo Installing Dynamsoft Barcode Reader SDK...
pip install dynamsoft-barcode-reader

echo.
echo Installing OpenCV for webcam support...
pip install opencv-python

echo.
echo Installing optional QR code generator for testing...
pip install qrcode[pil]

echo.
echo ============================================
echo Running Tests
echo ============================================

REM Run the test script
python test_scanner.py

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo You can now use the barcode scanner with commands like:
echo.
echo   python barcode_scanner.py --image path\to\image.jpg
echo   python barcode_scanner.py --webcam
echo   python barcode_scanner.py --folder path\to\folder\
echo.
echo For more options, run:
echo   python barcode_scanner.py --help
echo.
pause