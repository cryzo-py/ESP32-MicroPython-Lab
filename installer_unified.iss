
#define MyAppName "ESP32 MicroPython Lab"
#define MyAppVersion "3.0"
#define MyAppPublisher "ESP32Lab"
#define MyAppURL "https://github.com/faresbelhaj/esp32_lab"

[Setup]
AppId={{D37E60E6-ABCD-1234-87A5-E12345678901}
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
OutputBaseFilename=ESP32_MicroPython_Lab_Setup_v3.0
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
SetupIconFile=esp32_lab\resources\icons\app_icon.ico
UninstallDisplayIcon={app}\ESP32_Lab_Student.exe

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "student"; Description: "Installation Élève (Student Player)"; Flags: iscustom
Name: "teacher"; Description: "Installation Enseignant (Teacher Studio)"

[Components]
Name: "student_comp"; Description: "Lecteur Élève"; Types: student
Name: "teacher_comp"; Description: "Studio Enseignant"; Types: teacher

[Files]
; Fichiers partagés (Ressources, Readme, etc)
Source: "dist\ESP32_Lab_Student\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: student_comp
Source: "dist\ESP32_Lab_Teacher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: teacher_comp
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ESP32 Lab - Student Player"; Filename: "{app}\ESP32_Lab_Student.exe"; Components: student_comp
Name: "{group}\ESP32 Lab - Teacher Studio"; Filename: "{app}\ESP32_Lab_Teacher.exe"; Components: teacher_comp
Name: "{group}\Documentation (README)"; Filename: "{app}\README.md"
Name: "{group}\Licence d'utilisation"; Filename: "{app}\LICENSE"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\ESP32 Lab - Student Player"; Filename: "{app}\ESP32_Lab_Student.exe"; Tasks: desktopicon; Components: student_comp
Name: "{autodesktop}\ESP32 Lab - Teacher Studio"; Filename: "{app}\ESP32_Lab_Teacher.exe"; Tasks: desktopicon; Components: teacher_comp

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Registry]
; Association de l'extension .lab32 pour s'ouvrir avec la version élève (par sécurité) ou prof si c'est la seule installée
Root: HKA; Subkey: "Software\Classes\.lab32"; ValueType: string; ValueName: ""; ValueData: "ESP32Lab.Project"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.lab32"; ValueType: string; ValueName: "Content Type"; ValueData: "application/x-esp32lab"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project"; ValueType: string; ValueName: ""; ValueData: "Projet ESP32 MicroPython Lab"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\ESP32_Lab_Student.exe"",0"

; Commande Student (si installé)
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ESP32_Lab_Student.exe"" ""%1"""; Components: student_comp
; Commande Teacher (si Student n'est pas installé)
Root: HKA; Subkey: "Software\Classes\ESP32Lab.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\ESP32_Lab_Teacher.exe"" ""%1"""; Components: teacher_comp

[Run]
Filename: "{app}\ESP32_Lab_Student.exe"; Description: "Lancer ESP32 Lab - Student"; Flags: nowait postinstall skipifsilent; Components: student_comp
Filename: "{app}\ESP32_Lab_Teacher.exe"; Description: "Lancer ESP32 Lab - Teacher"; Flags: nowait postinstall skipifsilent; Components: teacher_comp
