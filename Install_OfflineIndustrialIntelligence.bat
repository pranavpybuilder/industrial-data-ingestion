@echo off
REM ============================================================================
REM Offline Industrial Intelligence Platform - Installation Script
REM Version 1.0
REM ============================================================================

setlocal enabledelayedexpansion
cls

REM Check for Administrator rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ============================================================================
    echo ERROR: This installer requires Administrator privileges.
    echo ============================================================================
    echo.
    echo Right-click on this script and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Initialize
set PRODUCT_NAME=Offline Industrial Intelligence
set PRODUCT_VERSION=1.0.0
set INSTALL_DIR=%ProgramFiles%\OfflineIndustrialIntelligence
set SOURCE_DIR=%~dp0dist\OfflineIndustrialIntelligence

cls
echo.
echo ============================================================================
echo %PRODUCT_NAME% v%PRODUCT_VERSION% - Installation Wizard
echo ============================================================================
echo.
echo This wizard will install %PRODUCT_NAME% on your computer.
echo.
echo Installation Details:
echo   - Destination: %INSTALL_DIR%
echo   - Type: Standalone Application (No external dependencies)
echo   - Size: ~60 MB
echo.
echo ============================================================================
echo.

REM Check if source exists
if not exist "%SOURCE_DIR%" (
    echo ERROR: Source files not found at:
    echo %SOURCE_DIR%
    echo.
    echo Please ensure the 'dist\OfflineIndustrialIntelligence' folder exists.
    echo.
    pause
    exit /b 1
)

REM Check if already installed
if exist "%INSTALL_DIR%" (
    echo %PRODUCT_NAME% is already installed at:
    echo %INSTALL_DIR%
    echo.
    set /p REPLACE="Do you want to replace it? (Y/N): "
    if /i not "!REPLACE!"=="Y" (
        echo Installation cancelled.
        pause
        exit /b 0
    )
    echo.
    echo Removing existing installation...
    rmdir /s /q "%INSTALL_DIR%" 2>nul
    timeout /t 1 /nobreak >nul
)

REM Create installation directory
echo.
echo Creating installation directory...
mkdir "%INSTALL_DIR%" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to create installation directory.
    echo Verify you have permission to write to Program Files.
    pause
    exit /b 1
)

REM Copy files
echo Copying application files...
xcopy "%SOURCE_DIR%\*" "%INSTALL_DIR%\" /E /I /Y /Q >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to copy files.
    pause
    exit /b 1
)

REM Create shortcut helper (VBScript)
set SHORTCUT_SCRIPT=%TEMP%\create_shortcuts.vbs
(
    echo Set oWS = WScript.CreateObject("WScript.Shell"^)
    echo sDesktop = oWS.SpecialFolders("Desktop"^)
    echo sStartMenu = oWS.SpecialFolders("StartMenu"^)
    echo.
    echo REM Create Desktop shortcut
    echo Set oLink = oWS.CreateShortcut(sDesktop ^& "\%PRODUCT_NAME%.lnk"^)
    echo oLink.TargetPath = "%INSTALL_DIR%\OfflineIndustrialIntelligence.exe"
    echo oLink.WorkingDirectory = "%INSTALL_DIR%"
    echo oLink.IconLocation = "%INSTALL_DIR%\OfflineIndustrialIntelligence.exe"
    echo oLink.Save
    echo.
    echo REM Create Start Menu folder
    echo Set objFSO = CreateObject("Scripting.FileSystemObject"^)
    echo sStartMenuApp = sStartMenu ^& "\%PRODUCT_NAME%"
    echo if not objFSO.FolderExists(sStartMenuApp^) then
    echo   objFSO.CreateFolder(sStartMenuApp^)
    echo end if
    echo.
    echo REM Create Start Menu shortcut
    echo Set oLink = oWS.CreateShortcut(sStartMenuApp ^& "\%PRODUCT_NAME%.lnk"^)
    echo oLink.TargetPath = "%INSTALL_DIR%\OfflineIndustrialIntelligence.exe"
    echo oLink.WorkingDirectory = "%INSTALL_DIR%"
    echo oLink.IconLocation = "%INSTALL_DIR%\OfflineIndustrialIntelligence.exe"
    echo oLink.Save
    echo.
    echo REM Create Uninstall shortcut
    echo Set oLink = oWS.CreateShortcut(sStartMenuApp ^& "\Uninstall.lnk"^)
    echo oLink.TargetPath = "%INSTALL_DIR%\Uninstall.bat"
    echo oLink.Save
) > "%SHORTCUT_SCRIPT%"

echo Creating shortcuts...
cscript.exe //nologo "%SHORTCUT_SCRIPT%" >nul 2>&1
if exist "%SHORTCUT_SCRIPT%" del "%SHORTCUT_SCRIPT%"

REM Register in Add/Remove Programs (Registry)
echo Registering application...
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\%PRODUCT_NAME%" ^
    /v DisplayName /d "%PRODUCT_NAME%" /f >nul 2>&1
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\%PRODUCT_NAME%" ^
    /v UninstallString /d "%INSTALL_DIR%\Uninstall.bat" /f >nul 2>&1
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\%PRODUCT_NAME%" ^
    /v DisplayVersion /d "%PRODUCT_VERSION%" /f >nul 2>&1
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\%PRODUCT_NAME%" ^
    /v Publisher /d "Industrial Maintenance Systems" /f >nul 2>&1

REM Create Uninstall script
echo Creating uninstaller...
(
    echo @echo off
    echo set INSTALL_DIR=%INSTALL_DIR%
    echo set PRODUCT_NAME=%PRODUCT_NAME%
    echo.
    echo cls
    echo echo.
    echo echo ============================================================================
    echo echo Uninstalling !PRODUCT_NAME!...
    echo echo ============================================================================
    echo echo.
    echo.
    echo REM Uninstall confirmation
    echo set /p CONFIRM="Are you sure you want to uninstall !PRODUCT_NAME!? (Y/N): "
    echo if /i not "!CONFIRM!"=="Y" (
    echo     echo Uninstall cancelled.
    echo     pause
    echo     exit /b 0
    echo ^)
    echo.
    echo echo Removing installation files...
    echo rmdir /s /q "!INSTALL_DIR!" 2^>nul
    echo.
    echo echo Removing Start Menu shortcut...
    echo rmdir /s /q "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\!PRODUCT_NAME!" 2^>nul
    echo.
    echo echo Removing Desktop shortcut...
    echo del "%%USERPROFILE%%\Desktop\!PRODUCT_NAME!.lnk" 2^>nul
    echo.
    echo echo Removing registry entries...
    echo reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\!PRODUCT_NAME!" /f 2^>nul
    echo.
    echo echo ============================================================================
    echo echo Uninstallation Complete!
    echo echo ============================================================================
    echo echo.
    echo pause
) > "%INSTALL_DIR%\Uninstall.bat"

REM Success message
cls
echo.
echo ============================================================================
echo INSTALLATION COMPLETE!
echo ============================================================================
echo.
echo %PRODUCT_NAME% v%PRODUCT_VERSION% has been successfully installed.
echo.
echo Location: %INSTALL_DIR%
echo.
echo Shortcuts created:
echo   - Desktop: %PRODUCT_NAME%.lnk
echo   - Start Menu: %PRODUCT_NAME%
echo.
echo To launch the application:
echo   1. Double-click the desktop shortcut, OR
echo   2. Use Start Menu: %PRODUCT_NAME%, OR
echo   3. Run: %INSTALL_DIR%\OfflineIndustrialIntelligence.exe
echo.
echo To uninstall:
echo   - Use: Start Menu ^> %PRODUCT_NAME% ^> Uninstall, OR
echo   - Use: Settings ^> Apps ^> %PRODUCT_NAME% ^> Uninstall
echo.
echo ============================================================================
echo.

REM Offer to launch application
set /p LAUNCH="Do you want to launch %PRODUCT_NAME% now? (Y/N): "
if /i "!LAUNCH!"=="Y" (
    echo.
    echo Launching %PRODUCT_NAME%...
    start "" "%INSTALL_DIR%\OfflineIndustrialIntelligence.exe"
)

echo.
echo Thank you for installing %PRODUCT_NAME%!
echo.
pause
exit /b 0
