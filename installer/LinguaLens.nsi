Unicode true
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "WinVer.nsh"

!define APP_NAME "语镜 LinguaLens"
!define APP_EXE "LinguaLens.exe"
!define APP_VERSION "2.0.0"
!define APP_PUBLISHER "大肥鱼 / LinguaLens"
!define APP_ID "LinguaLens"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\LinguaLens"
!define MUI_ICON "..\web\assets\语镜.ico"
!define MUI_UNICON "..\web\assets\语镜.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "立即打开语镜"

Name "${APP_NAME}"
OutFile "..\dist\语镜LinguaLens-Setup-${APP_VERSION}.exe"
InstallDir "$LOCALAPPDATA\Programs\LinguaLens"
InstallDirRegKey HKCU "Software\LinguaLens" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 64
BrandingText "语镜 LinguaLens · 读懂每一句的骨架"

VIProductVersion "2.0.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "${APP_NAME}"
VIAddVersionKey /LANG=2052 "FileDescription" "语镜 LinguaLens 安装程序"
VIAddVersionKey /LANG=2052 "FileVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=2052 "ProductVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=2052 "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Copyright (c) 2026"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

Section "语镜 LinguaLens" SecMain
  SetOutPath "$INSTDIR"
  SetOverwrite on
  File /r "..\dist\LinguaLens\*.*"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\语镜 LinguaLens"
  CreateShortcut "$SMPROGRAMS\语镜 LinguaLens\语镜 LinguaLens.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
  CreateShortcut "$SMPROGRAMS\语镜 LinguaLens\卸载语镜.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\语镜 LinguaLens.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

  WriteRegStr HKCU "Software\LinguaLens" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "${UNINST_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "${UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${UNINST_KEY}" "QuietUninstallString" "$INSTDIR\Uninstall.exe /S"
  WriteRegDWORD HKCU "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINST_KEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "%u" $0
  WriteRegDWORD HKCU "${UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\语镜 LinguaLens.lnk"
  Delete "$SMPROGRAMS\语镜 LinguaLens\语镜 LinguaLens.lnk"
  Delete "$SMPROGRAMS\语镜 LinguaLens\卸载语镜.lnk"
  RMDir "$SMPROGRAMS\语镜 LinguaLens"
  DeleteRegKey HKCU "${UNINST_KEY}"
  DeleteRegKey HKCU "Software\LinguaLens"

  IfSilent KeepData
  MessageBox MB_YESNO|MB_ICONQUESTION "是否同时删除语镜的历史记录、设置和缓存？$\r$\n选择“否”会保留你的文章与配置。" IDNO KeepData
  RMDir /r "$LOCALAPPDATA\LinguaLens"
  KeepData:
  RMDir /r "$INSTDIR"
SectionEnd
