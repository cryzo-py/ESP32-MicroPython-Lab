Write-Host "Construction des exécutables (PyInstaller)..." -ForegroundColor Cyan
pyinstaller -y "D:\Projets\ESP32 Lab\esp32_lab.spec"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Génération de l'installateur Élève..." -ForegroundColor Green
    & "C:\Users\bel-h\AppData\Local\Programs\Inno Setup 6\iscc.exe" "D:\Projets\ESP32 Lab\installer_student.iss"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Génération de l'installateur Enseignant..." -ForegroundColor Green
        & "C:\Users\bel-h\AppData\Local\Programs\Inno Setup 6\iscc.exe" "D:\Projets\ESP32 Lab\installer_teacher.iss"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Les deux installateurs ont été générés avec succès dans le dossier 'dist_installer' !" -ForegroundColor Green
        } else {
            Write-Host "Erreur lors de la création de l'installateur Enseignant." -ForegroundColor Red
        }
    } else {
        Write-Host "Erreur lors de la création de l'installateur Élève." -ForegroundColor Red
    }
} else {
    Write-Host "Erreur lors de l'exécution de PyInstaller." -ForegroundColor Red
}
