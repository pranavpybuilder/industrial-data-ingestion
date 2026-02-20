; NSIS Installer Script for Offline Industrial Intelligence Platform
; Version 1.0

!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"

; ============================================================================
; INSTALLER SETTINGS
; ============================================================================

!define PRODUCT_NAME "Offline Industrial Intelligence"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Industrial Maintenance Systems"
!define PRODUCT_WEB_SITE "https://industrialmaintenance.local"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\OfflineIndustrialIntelligence.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

InstallDir "$PROGRAMFILES\OfflineIndustrialIntelligence"

RequestExecutionLevel admin

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "OfflineIndustrialIntelligence_Setup_v${PRODUCT_VERSION}.exe"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

BrandingText "© 2026 Industrial Maintenance Systems"
Icon "app_icon.ico"

; ============================================================================
; MUI SETTINGS
; ============================================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ============================================================================
; INSTALLER SECTIONS
; ============================================================================

Section "Install Application"
  SetOverwrite on
  SetOutPath "$INSTDIR"

  ; Copy files
  File /r "dist\OfflineIndustrialIntelligence\*.*"

  ; Registry Entries
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\OfflineIndustrialIntelligence.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"

  ; Calculate install size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"

  ; Create Uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; IMPORTANT FIX: Make shortcuts for ALL USERS
  SetShellVarContext all

  ; Start Menu Shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\OfflineIndustrialIntelligence.exe"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

  ; Desktop Shortcut
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\OfflineIndustrialIntelligence.exe"

  DetailPrint "Installation Complete!"

SectionEnd

; ============================================================================
; UNINSTALLER SECTION
; ============================================================================

Section "Uninstall"

  ; IMPORTANT FIX: Same context for uninstall
  SetShellVarContext all

  ; Remove files
  RMDir /r "$INSTDIR"

  ; Remove shortcuts
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"

  ; Remove registry
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  DetailPrint "Uninstallation Complete!"

SectionEnd

; ============================================================================
; INSTALLER FUNCTIONS
; ============================================================================

Function .onInit
  ReadRegStr $0 HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
  ${If} $0 != ""
    MessageBox MB_YESNO|MB_ICONQUESTION "$(^Name) is already installed.$\n$\nDo you want to replace it?" IDYES reinstall IDNO abort
    reinstall:
      ExecWait '$0 _?=$INSTDIR'
    abort:
      Quit
  ${EndIf}
FunctionEnd

Function .onInstSuccess
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) has been successfully installed!$\n$\nAn icon has been placed on your desktop for quick access."
FunctionEnd