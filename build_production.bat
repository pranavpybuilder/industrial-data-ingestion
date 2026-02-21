@echo off
REM Production Build Script
REM Offline Industrial Data Intelligence System
REM =========================================

cd /d "%~dp0"

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist main.spec del main.spec

echo.
echo ========================================
echo BUILDING PRODUCTION EXECUTABLE
echo ========================================
echo Using: --onedir for faster packaging
echo With: Icon, offline resources, hidden imports
echo.

echo Starting build...
"venv\Scripts\python.exe" -m PyInstaller ^
  --onedir ^
  --windowed ^
  --noconfirm ^
  --icon=app_icon.ico ^
  --name OfflineIndustrialIntelligence ^
  --add-data "frontend/electron_app/renderer/dist;frontend/electron_app/renderer/dist" ^
  --add-data "storage/schema.sql;storage" ^
  --hidden-import sklearn ^
  --hidden-import scipy ^
  --hidden-import duckdb ^
  --hidden-import pandas ^
  --hidden-import numpy ^
  --hidden-import PySide6.QtWebEngineWidgets ^
  --collect-all PySide6 ^
  --collect-all sklearn ^
  --collect-all scipy ^
  frontend/electron_app/main/main.py

echo.
echo ========================================
if exist "dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe" (
    echo [SUCCESS] Build complete!
    echo.
    echo Executable: dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe
    dir "dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe"
    echo.
    echo To run: dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe
) else (
    echo [FAILED] Build did not complete
    echo Check console output above for errors
)

pause
