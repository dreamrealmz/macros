!define APP_NAME "macros"
!define APP_VERSION "1.0"
!define INSTALL_DIR "$PROGRAMFILES\${APP_NAME}"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "setup.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

Section
    SetOutPath "$INSTDIR"
    File "dist\main.exe"
    CreateDirectory "$DESKTOP"
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\main.exe" ""
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir "$INSTDIR"
SectionEnd
