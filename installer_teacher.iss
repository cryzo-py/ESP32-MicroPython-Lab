#define MyAppName "ESP32 MicroPython Lab - Teacher"
#define MyAppVersion "3.0"
#define MyAppPublisher "ESP32Lab"
#define MyAppURL "https://github.com/faresbelhaj/esp32_lab"

[Setup]
AppId={{D37E60E6-ABCD-1234-87A5-TEACHER1234}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
PrivilegesRequired=lowest
OutputDir=dist_installer
OutputBaseFilename=ESP32_MicroPython_Lab_Teacher_v3.0
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
SetupIconFile=esp32_lab\resources\icons\app_icon.ico
UninstallDisplayIcon={app}\ESP32_Lab_Teacher.exe

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\ESP32_Lab_Teacher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ESP32 Lab - Teacher Studio"; Filename: "{app}\ESP32_Lab_Teacher.exe"
Name: "{group}\Documentation (README)"; Filename: "{app}\README.md"
Name: "{group}\Licence d'utilisation"; Filename: "{app}\LICENSE"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\ESP32 Lab - Teacher Studio"; Filename: "{app}\ESP32_Lab_Teacher.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Registry]
Root: HKA; Subkey: "Software\Classes\.lab32"; ValueType: string; ValueName: ""; ValueData: "ESP32Lab.Project"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.lab32"; ValueType: string; ValueName: "Content Type"; ValueData: "application/x-esp32lab"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project"; ValueType: string; ValueName: ""; ValueData: "Projet ESP32 MicroPython Lab"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\ESP32_Lab_Teacher.exe"",0"
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ESP32_Lab_Teacher.exe"" ""%1"""

[Run]
Filename: "{app}\ESP32_Lab_Teacher.exe"; Description: "Lancer ESP32 Lab - Teacher Studio"; Flags: nowait postinstall skipifsilent
