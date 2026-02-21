@echo off
REM =========================================================
REM  Offline Industrial Intelligence - Full Build Pipeline
REM  1. Build frontend (Vite/React)
REM  2. Build Python exe (PyInstaller --onedir)
REM  3. Build installer (NSIS)
REM =========================================================

cd /d "%~dp0"

echo ========================================
echo  STEP 0: Pre-flight checks
echo ========================================
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found. Run: python -m venv venv
    pause & exit /b 1
)
if not exist "app_icon.ico" (
    echo [ERROR] app_icon.ico not found in project root.
    pause & exit /b 1
)
if not exist "frontend\electron_app\main\main.py" (
    echo [ERROR] frontend entry point not found.
    pause & exit /b 1
)

echo.
echo ========================================
echo  STEP 1: Build Frontend (Vite/React)
echo ========================================
if exist "frontend\electron_app\renderer\package.json" (
    pushd frontend\electron_app\renderer
    if not exist node_modules (
        echo Installing npm dependencies...
        call npm install
    )
    echo Building frontend...
    call npm run build
    popd
) else (
    echo [SKIP] No package.json found, using existing dist/
)
if not exist "frontend\electron_app\renderer\dist\index.html" (
    echo [ERROR] Frontend dist not found. Build failed.
    pause & exit /b 1
)
echo [OK] Frontend dist ready.

echo.
echo ========================================
echo  STEP 2: Build PyInstaller Bundle
echo ========================================
echo Cleaning previous builds...
if exist build rmdir /s /q build 2>nul
if exist dist  rmdir /s /q dist  2>nul
if exist main.spec del main.spec 2>nul

echo Building with PyInstaller (--onedir)...
"venv\Scripts\python.exe" -m PyInstaller ^
  --onedir ^
  --windowed ^
  --noconfirm ^
  --icon=app_icon.ico ^
  --name OfflineIndustrialIntelligence ^
  --add-data "frontend/electron_app/renderer/dist;frontend/electron_app/renderer/dist" ^
  --add-data "storage/schema.sql;storage" ^
  --add-data "ingestion/contracts;ingestion/contracts" ^
  --add-data "data/sample;data/sample" ^
  --hidden-import sklearn ^
  --hidden-import sklearn.ensemble ^
  --hidden-import sklearn.ensemble._iforest ^
  --hidden-import scipy ^
  --hidden-import scipy.stats ^
  --hidden-import duckdb ^
  --hidden-import pandas ^
  --hidden-import numpy ^
  --hidden-import openpyxl ^
  --hidden-import reportlab ^
  --hidden-import PySide6.QtWebEngineWidgets ^
  --hidden-import PySide6.QtWebChannel ^
  --collect-all PySide6 ^
  --collect-all sklearn ^
  --collect-all scipy ^
  frontend/electron_app/main/main.py

echo.
if not exist "dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe" (
    echo [FAILED] PyInstaller build failed. Check output above.
    pause & exit /b 1
)
echo [OK] PyInstaller build complete.
for %%I in ("dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe") do echo   EXE size: %%~zI bytes

echo.
echo ========================================
echo  STEP 3: Build NSIS Installer
echo ========================================
where makensis >nul 2>&1
if %errorlevel% neq 0 (
    echo [SKIP] NSIS (makensis) not found on PATH.
    echo.
    echo To build the installer manually:
    echo   1. Install NSIS from https://nsis.sourceforge.io/Download
    echo   2. Run: makensis OfflineIndustrialIntelligence_Installer.nsi
    echo.
    echo The PyInstaller output is ready at:
    echo   dist\OfflineIndustrialIntelligence\
    echo.
    pause & exit /b 0
)

echo Running NSIS compiler...
makensis OfflineIndustrialIntelligence_Installer.nsi
if %errorlevel% neq 0 (
    echo [FAILED] NSIS build failed.
    pause & exit /b 1
)

echo.
echo ========================================
echo  BUILD COMPLETE
echo ========================================
echo.
echo  Installer: OfflineIndustrialIntelligence_Setup_v1.0.0.exe
echo  Portable:  dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe
echo.
pause
