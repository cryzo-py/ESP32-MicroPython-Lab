# ==============================================================================
# Script de compilation et packaging automatisé de release — ESP32 & Arduino Lab v4.0
# Auteur : Fares Bel Haj Ali
# ==============================================================================

param(
    [switch]$SkipInstaller = $false,
    [switch]$Clean = $true
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   COMPILATION RELEASE V4.0 - ESP32 & ARDUINO LAB        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Répertoire racine : $RootDir"

Set-Location $RootDir

# 1. Nettoyage des anciens dossiers de build si demandé
if ($Clean) {
    Write-Host "`n[1/4] Nettoyage des répertoires 'build' et 'dist'..." -ForegroundColor Yellow
    if (Test-Path "$RootDir\build") { Remove-Item -Path "$RootDir\build" -Recurse -Force }
    if (Test-Path "$RootDir\dist") { Remove-Item -Path "$RootDir\dist" -Recurse -Force }
}

# 2. Exécution de PyInstaller avec la configuration spec
Write-Host "`n[2/4] Compilation des binaires autonomes via PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller "$RootDir\esp32_lab.spec" --noconfirm

# 3. Vérification de l'intégrité des exécutables générés
Write-Host "`n[3/4] Vérification de l'intégrité des exécutables produits..." -ForegroundColor Yellow

$StudentExe = "$RootDir\dist\ESP32_Arduino_Lab_Student\ESP32_Arduino_Lab_Student.exe"
$TeacherExe = "$RootDir\dist\ESP32_Arduino_Lab_Teacher_Studio\ESP32_Arduino_Lab_Teacher_Studio.exe"

if (-not (Test-Path $StudentExe)) {
    Write-Error "Échec de génération : L'exécutable Élève ($StudentExe) est introuvable !"
}
if (-not (Test-Path $TeacherExe)) {
    Write-Error "Échec de génération : L'exécutable Enseignant ($TeacherExe) est introuvable !"
}

$StudentSize = (Get-Item $StudentExe).Length / 1MB
$TeacherSize = (Get-Item $TeacherExe).Length / 1MB

Write-Host " -> ESP32_Arduino_Lab_Student.exe        : OK ($([math]::Round($StudentSize, 2)) MB)" -ForegroundColor Green
Write-Host " -> ESP32_Arduino_Lab_Teacher_Studio.exe : OK ($([math]::Round($TeacherSize, 2)) MB)" -ForegroundColor Green

# 4. Compilation des installeurs Inno Setup si l'outil est installé
if (-not $SkipInstaller) {
    Write-Host "`n[4/4] Recherche du compilateur Inno Setup (ISCC)..." -ForegroundColor Yellow
    
    $InnoCandidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\iscc.exe",
        "${env:ProgramFiles}\Inno Setup 6\iscc.exe",
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\iscc.exe",
        "C:\Inno Setup 6\iscc.exe"
    )
    
    $IsccPath = $null
    foreach ($cand in $InnoCandidates) {
        if (Test-Path $cand) {
            $IsccPath = $cand
            break
        }
    }
    
    if ($IsccPath) {
        Write-Host "Compilateur Inno Setup détecté : $IsccPath" -ForegroundColor Cyan
        if (-not (Test-Path "$RootDir\dist_installer")) {
            New-Item -ItemType Directory -Path "$RootDir\dist_installer" | Out-Null
        }

        Write-Host "Génération de l'installeur Élève..."
        & $IsccPath "$RootDir\installer_student.iss"

        Write-Host "Génération de l'installeur Enseignant..."
        & $IsccPath "$RootDir\installer_teacher.iss"

        Write-Host "Installeurs générés avec succès dans le dossier 'dist_installer\'." -ForegroundColor Green
    } else {
        Write-Host "Inno Setup (ISCC.exe) non trouvé. Les dossiers autonomes sont prêts dans 'dist/'." -ForegroundColor DarkYellow
        Write-Host "Pour créer des installeurs .exe tout-en-un, installez Inno Setup 6 : https://jrsoftware.org/isdl.php" -ForegroundColor DarkGray
    }
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   PACKAGING V4.0 TERMINÉ AVEC SUCCÈS !                   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
