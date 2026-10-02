; Inno Setup Script for MNIME
; Builds a standard Windows standalone installer (MNIME_Setup.exe)

[Setup]
AppName=MNIME
AppVersion=Final
AppPublisher=MNIME
AppPublisherURL=https://MNIME.app
DefaultDirName={localappdata}\Programs\MNIME
DefaultGroupName=MNIME
OutputDir=installer
OutputBaseFilename=MNIME_Setup
SetupIconFile=OMN.ico
LicenseFile=LICENSE
#ifdef SignInstaller
SignTool=MySignTool
#endif
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\OMN.ico

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\MNIME\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "OMN.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MNIME"; Filename: "{app}\MNIME.exe"; IconFilename: "{app}\OMN.ico"
Name: "{group}\Uninstall MNIME"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MNIME"; Filename: "{app}\MNIME.exe"; IconFilename: "{app}\OMN.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\MNIME.exe"; Description: "Launch MNIME"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
