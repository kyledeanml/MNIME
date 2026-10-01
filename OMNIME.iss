; Inno Setup Script for OMNIME
; Builds a standard Windows standalone installer (OMNIME_Setup.exe)

[Setup]
AppName=OMNIME
AppVersion=99
AppPublisher=OMNIME
AppPublisherURL=https://omnime.app
DefaultDirName={localappdata}\Programs\OMNIME
DefaultGroupName=OMNIME
OutputDir=installer
OutputBaseFilename=OMNIME_Setup_v99
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
Source: "dist\OMNIME\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "OMN.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\OMNIME"; Filename: "{app}\OMNIME.exe"; IconFilename: "{app}\OMN.ico"
Name: "{group}\Uninstall OMNIME"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OMNIME"; Filename: "{app}\OMNIME.exe"; IconFilename: "{app}\OMN.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\OMNIME.exe"; Description: "Launch OMNIME"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
