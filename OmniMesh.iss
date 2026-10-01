; Inno Setup Script for OmniMesh
; Builds a standard Windows standalone installer (OmniMesh_Setup.exe)

[Setup]
AppName=OmniMesh
AppVersion=2.1
AppPublisher=OmniMesh
AppPublisherURL=https://omnimesh.app
DefaultDirName={localappdata}\Programs\OmniMesh
DefaultGroupName=OmniMesh
OutputDir=installer
OutputBaseFilename=OmniMesh_Setup_v2.1
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
Source: "dist\OmniMesh\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "OMN.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\OmniMesh"; Filename: "{app}\OmniMesh.exe"; IconFilename: "{app}\OMN.ico"
Name: "{group}\Uninstall OmniMesh"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OmniMesh"; Filename: "{app}\OmniMesh.exe"; IconFilename: "{app}\OMN.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\OmniMesh.exe"; Description: "Launch OmniMesh"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
