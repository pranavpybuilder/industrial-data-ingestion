; ===========================================================================
; NSIS Installer Script - Offline Industrial Intelligence Platform
; Version 1.0.0
;
; This script packages the PyInstaller --onedir output into a single
; self-extracting installer (.exe). When the user runs the installer it
; extracts to Program Files, creates shortcuts, and registers uninstall.
; ===========================================================================

!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"

; ---------------------------------------------------------------------------
; Product metadata
; ---------------------------------------------------------------------------
!define PRODUCT_NAME        "Offline Industrial Intelligence"
!define PRODUCT_VERSION     "1.0.0"
!define PRODUCT_PUBLISHER   "Industrial Maintenance Systems"
!define PRODUCT_WEB_SITE    "https://industrialmaintenance.local"
!define PRODUCT_EXE         "OfflineIndustrialIntelligence.exe"
!define PRODUCT_DIR_REGKEY  "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_EXE}"
!define PRODUCT_UNINST_KEY  "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

; ---------------------------------------------------------------------------
; Installer configuration
; ---------------------------------------------------------------------------
Name          "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile       "OfflineIndustrialIntelligence_Setup_v${PRODUCT_VERSION}.exe"
InstallDir    "$PROGRAMFILES\OfflineIndustrialIntelligence"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""

RequestExecutionLevel admin
SetCompressor /SOLID lzma
SetCompressorDictSize 64

BrandingText  "(c) 2026 Industrial Maintenance Systems"
Icon          "app_icon.ico"

ShowInstDetails   show
ShowUnInstDetails show

; ---------------------------------------------------------------------------
; MUI pages
; ---------------------------------------------------------------------------
!define MUI_ICON   "app_icon.ico"
!define MUI_UNICON "app_icon.ico"

!define MUI_WELCOMEPAGE_TITLE "Welcome to ${PRODUCT_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT  "This wizard will install ${PRODUCT_NAME} v${PRODUCT_VERSION} on your computer.$\r$\n$\r$\nThe application runs fully offline - no internet connection is required after installation.$\r$\n$\r$\nClick Next to continue."

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${PRODUCT_NAME}"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ===========================================================================
; INSTALL SECTION
; ===========================================================================
Section "Install"
    SetOverwrite on
    SetOutPath "$INSTDIR"

    ; Copy the entire PyInstaller --onedir output
    File /r "dist\OfflineIndustrialIntelligence\*.*"

    ; Create writable data directories for runtime use
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\data\raw"
    CreateDirectory "$INSTDIR\data\sample"
    CreateDirectory "$INSTDIR\data\exports"
    CreateDirectory "$INSTDIR\logs"

    ; --- Registry ---
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${PRODUCT_EXE}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName"     "${PRODUCT_NAME}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon"     "$INSTDIR\${PRODUCT_EXE}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion"  "${PRODUCT_VERSION}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher"       "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout"    "${PRODUCT_WEB_SITE}"

    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"

    ; --- Uninstaller ---
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; --- Shortcuts (all users) ---
    SetShellVarContext all
    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut  "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0
    CreateShortCut  "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortCut  "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXE}" "" "$INSTDIR\${PRODUCT_EXE}" 0

    DetailPrint "Installation complete!"
SectionEnd

; ===========================================================================
; UNINSTALL SECTION
; ===========================================================================
Section "Uninstall"
    SetShellVarContext all

    ; Remove application files
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
    Delete   "$DESKTOP\${PRODUCT_NAME}.lnk"

    ; Remove registry entries
    DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

    DetailPrint "Uninstallation complete!"
SectionEnd

; ===========================================================================
; CALLBACKS
; ===========================================================================
Function .onInit
    ; Check for existing installation
    ReadRegStr $0 HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
    ${If} $0 != ""
        MessageBox MB_YESNO|MB_ICONQUESTION \
            "$(^Name) is already installed.$\n$\nRemove previous installation first?" \
            IDYES do_uninstall IDNO abort_install
        do_uninstall:
            ExecWait '$0 _?=$INSTDIR'
            Goto done
        abort_install:
            Abort
        done:
    ${EndIf}
FunctionEnd

Function .onInstSuccess
    ; Silent - the MUI finish page handles the success message
FunctionEnd