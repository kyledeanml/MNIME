; Inno Setup Script for MNIME
; Builds a standard Windows standalone installer (MNIME_Setup.exe)

[Setup]
AppName=MNIME
AppVersion=2.1
AppPublisher=MNIME
AppPublisherURL=https://MNIME.app
DefaultDirName={localappdata}\Programs\MNIME
DefaultGroupName=MNIME
OutputDir=installer
OutputBaseFilename=MNIME_Setup
SetupIconFile=MN.ico
LicenseFile=LICENSE
#ifdef SignInstaller
SignTool=MySignTool
#endif
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\MN.ico

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\MNIME\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "MN.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MNIME"; Filename: "{app}\MNIME.exe"; IconFilename: "{app}\MN.ico"
Name: "{group}\Uninstall MNIME"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MNIME"; Filename: "{app}\MNIME.exe"; IconFilename: "{app}\MN.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\MNIME.exe"; Description: "Launch MNIME"; Flags: nowait postinstall skipifsilent

[Registry]
; Register application presentation so PDFs show document page preview instead of MNIME logo
Root: HKCU; Subkey: "Software\Classes\Applications\MNIME.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "MNIME"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Applications\MNIME.exe"; ValueType: dword; ValueName: "Treatment"; ValueData: "2"
Root: HKCU; Subkey: "Software\Classes\Applications\MNIME.exe\DefaultIcon"; ValueType: expandsz; ValueData: "%SystemRoot%\System32\imageres.dll,-102"
Root: HKCU; Subkey: "Software\Classes\Applications\MNIME.exe\SupportedTypes"; ValueType: string; ValueName: ".pdf"; ValueData: ""
Root: HKCU; Subkey: "Software\Classes\Applications\MNIME.exe\shell\open\command"; ValueType: string; ValueData: """{app}\MNIME.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\Applications\MNIME.exe\ShellEx\{{8895b1c6-b41f-4c1c-a562-0d564250836f}"; ValueType: string; ValueData: "{3A84F9C2-6164-485C-A7D9-4B27F8AC009E}"

; Uninstaller cleanup of user settings, autorun, and file extension entries
Root: HKCU; Subkey: "Software\MNIME"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\MNIME.Document"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "MNIME"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.pdf\OpenWithProgids"; ValueName: "Applications\MNIME.exe"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.pdf\OpenWithProgids"; ValueName: "MNIME.Document"; Flags: uninsdeletevalue

[UninstallRun]
Filename: "{cmd}"; Parameters: "/c taskkill /F /IM MNIME.exe /T >nul 2>&1"; Flags: runhidden
Filename: "powershell"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$uc='HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.pdf\UserChoice'; if(Test-Path $uc){$prog=(Get-ItemProperty $uc -ErrorAction SilentlyContinue).ProgId; if($prog -like '*MNIME*'){Remove-Item -Path $uc -Recurse -Force -ErrorAction SilentlyContinue}}"""; Flags: runhidden
Filename: "ie4uinit.exe"; Parameters: "-show"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\MNIME"
