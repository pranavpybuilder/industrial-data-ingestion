@echo off
REM =========================================
REM Production Build Script
REM Offline Industrial Data Intelligence System
REM =========================================
REM
REM Usage:
REM   1. cd frontend\electron_app\renderer && npm run build
REM   2. Run this script from repo root: build_production.bat
REM   3. Compile NSIS installer:
REM      "C:\Program Files (x86)\NSIS\makensis.exe" OfflineIndustrialIntelligence_Installer.nsi
REM
REM Output: dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe

cd /d "%~dp0"

echo.
echo ============================================================
echo   OFFLINE INDUSTRIAL INTELLIGENCE - PRODUCTION BUILD
echo ============================================================
echo.

REM ── Step 1: Verify frontend is built ──────────────────────────
echo [1/3] Checking frontend build...
if not exist "frontend\electron_app\renderer\dist\index.html" (
    echo [ERROR] Frontend not built!
    echo Run: cd frontend\electron_app\renderer ^&^& npm run build
    pause
    exit /b 1
)
echo       Frontend dist/ found ✓

REM ── Step 2: Clean previous builds ─────────────────────────────
echo.
echo [2/3] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo       Clean ✓

REM ── Step 3: PyInstaller build ─────────────────────────────────
echo.
echo [3/3] Building with PyInstaller...
echo       Mode: --onedir (faster startup, easier debugging)
echo       Spec: OfflineIndustrialIntelligence.spec
echo.

python -m PyInstaller ^
  OfflineIndustrialIntelligence.spec ^
  --noconfirm ^
  --clean ^
  --log-level WARN

echo.
echo ============================================================
if exist "dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe" (
    echo   [SUCCESS] Build complete!
    echo.
    echo   Executable: dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe
    echo.
    dir "dist\OfflineIndustrialIntelligence\OfflineIndustrialIntelligence.exe"
    echo.
    echo   Next step: Compile NSIS installer
    echo   "C:\Program Files (x86)\NSIS\makensis.exe" OfflineIndustrialIntelligence_Installer.nsi
    echo.
) else (
    echo   [FAILED] Build did not produce executable.
    echo   Check console output above for errors.
    echo.
)
echo ============================================================

pause
