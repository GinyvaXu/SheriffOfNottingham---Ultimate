; Sheriff of Nottingham - Inno Setup installer script (v1.6.2)
; Compile: "C:\Users\zhenl\InnoSetup6\ISCC.exe" installer.iss

#define MyAppName "Sheriff of Nottingham"
#define MyAppVersion "1.6.2"
#define MyAppPublisher "Sheriff Project"
#define MyAppExeName "SheriffOfNottingham.exe"

[Setup]
AppId={{A5F65E7A-0E9A-4105-8033-A2E4BC39AAB2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
SetupIconFile=assets\icon.ico
; per-user install: silent auto-updates never need an elevation prompt
DefaultDirName={localappdata}\SheriffOfNottingham
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer
OutputBaseFilename=SheriffOfNottingham-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#MyAppVersion}
ChangesAssociations=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
; Let every local user enable/disable mods without admin rights, even when the
; game is installed under C:\Program Files (ACL protected).
Name: "{app}\mods"; Permissions: users-modify

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "mods\*"; DestDir: "{app}\mods"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the mods folder (including any mods the player added) on uninstall.
Type: filesandordirs; Name: "{app}\mods"
; Also clean up the per-user mods fallback folder (%APPDATA%).
Type: filesandordirs; Name: "{userappdata}\SheriffOfNottingham\mods"
