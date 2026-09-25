; =====================================================================
; Script Inno Setup 6 pour ESP32 MicroPython Lab
; Concepteur & Auteur : Fares Bel Haj Ali
; Email : belhadj.fares@gmail.com | Tél : +216 22 392 646
; =====================================================================

#define MyAppName "ESP32 MicroPython Lab"
#define MyAppVersion "3.0"
#define MyAppPublisher "Fares Bel Haj Ali"
#define MyAppURL "https://github.com/cryzo-py"
#define MyAppExeName "ESP32_Lab.exe"

[Setup]
; Identifiant d'application unique (GUID)
AppId={{D37E8675-9C4B-4E38-B9F2-C5784920FA81}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=mailto:belhadj.fares@gmail.com
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
ChangesAssociations=yes
PrivilegesRequired=lowest
OutputDir=dist_installer
OutputBaseFilename=ESP32_MicroPython_Lab_Setup_v3.0
SetupIconFile=esp32_lab\resources\icons\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion=3.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Laboratoire Virtuel ESP32 & MicroPython
VersionInfoCopyright=Copyright (C) 2024-2026 Fares Bel Haj Ali

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Inclusion de l'ensemble des fichiers générés par PyInstaller
Source: "dist\ESP32_Lab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "esp32_lab\resources\icons\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ESP32 Lab - Student Player"; Filename: "{app}\ESP32_Lab_Student.exe"; IconFilename: "{app}\app_icon.ico"; IconIndex: 0
Name: "{group}\ESP32 Lab - Teacher Studio"; Filename: "{app}\ESP32_Lab_Teacher.exe"; IconFilename: "{app}\app_icon.ico"; IconIndex: 0
Name: "{group}\Documentation (README)"; Filename: "{app}\README.md"
Name: "{group}\Licence d'utilisation"; Filename: "{app}\LICENSE"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\ESP32 Lab - Student"; Filename: "{app}\ESP32_Lab_Student.exe"; IconFilename: "{app}\app_icon.ico"; IconIndex: 0; Tasks: desktopicon
Name: "{autodesktop}\ESP32 Lab - Teacher"; Filename: "{app}\ESP32_Lab_Teacher.exe"; IconFilename: "{app}\app_icon.ico"; IconIndex: 0; Tasks: desktopicon

[Registry]
; Association automatique de l'extension .lab32 (et .esp32lab) à ESP32 MicroPython Lab (s'ouvre avec la version Student par défaut pour éviter les fuites)
Root: HKA; Subkey: "Software\Classes\.lab32"; ValueType: string; ValueName: ""; ValueData: "ESP32Lab.Project"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.lab32"; ValueType: string; ValueName: "Content Type"; ValueData: "application/x-esp32lab"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.esp32lab"; ValueType: string; ValueName: ""; ValueData: "ESP32Lab.Project"; Flags: uninsdeletevalue

; Définition du type de document, description, icône et commande d'ouverture
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project"; ValueType: string; ValueName: ""; ValueData: "Projet ESP32 MicroPython Lab"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\app_icon.ico,0"
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ESP32_Lab_Student.exe"" ""%1"""

; Préférence de langue choisie lors de l'installation (Français ou Anglais)
Root: HKCU; Subkey: "Software\ESP32Lab\ESP32MicroPythonLab"; ValueType: string; ValueName: "language"; ValueData: "fr"; Languages: french; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\ESP32Lab\ESP32MicroPythonLab"; ValueType: string; ValueName: "language"; ValueData: "en"; Languages: english; Flags: uninsdeletevalue

[Run]
Filename: "{app}\ESP32_Lab_Student.exe"; Description: "{cm:LaunchProgram,ESP32 Lab - Student}"; Flags: nowait postinstall skipifsilent
