@echo off
cd /d "c:\Users\Maintenance\Downloads\offline_endurance_intelligence"
REM First, clean old build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Starting PyInstaller build...
"venv\Scripts\python.exe" -m PyInstaller frontend/electron_app/main/main.py ^
  --onefile ^
  --windowed ^
  --noconfirm ^
  --icon=app_icon.ico ^
  --add-data "frontend/electron_app/renderer/dist;frontend/electron_app/renderer/dist" ^
  --hidden-import sklearn ^
  --hidden-import scipy ^
  --hidden-import duckdb ^
  --hidden-import pandas ^
  --hidden-import numpy ^
  --hidden-import PySide6.QtWebEngineWidgets ^
  --collect-all PySide6 ^
  --collect-all sklearn ^
  --collect-all scipy ^
  --verbose 2>&1 | tee build_output.log

echo.
echo Build Status:
if exist dist\main.exe (
    echo SUCCESS: main.exe created
    dir dist\main.exe
) else (
    echo FAILED: main.exe not found
    echo Checking for errors in build_output.log
    findstr /I "error" build_output.log
)
