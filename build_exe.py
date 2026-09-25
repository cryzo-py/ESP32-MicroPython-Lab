"""
Script de compilation automatisée de l'exécutable ESP32 MicroPython Lab
Auteur : Fares Bel Haj Ali
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Assurer l'encodage UTF-8 pour la console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def build():
    root_dir = Path(__file__).resolve().parent
    print("=" * 65)
    print(">> Compilation d'ESP32 MicroPython Lab (Executable Windows)")
    print("   Developpe par Fares Bel Haj Ali")
    print("=" * 65)

    spec_file = root_dir / "esp32_lab.spec"
    if not spec_file.exists():
        print(f"[ERREUR] Fichier spec introuvable ({spec_file})")
        sys.exit(1)

    # Nettoyage sélectif du dossier de build
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"

    print("\n[INFO] Lancement de PyInstaller avec esp32_lab.spec...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(spec_file),
    ]

    result = subprocess.run(cmd, cwd=str(root_dir))
    if result.returncode != 0:
        print("\n[ERREUR] Echec de la compilation avec PyInstaller.")
        sys.exit(result.returncode)

    output_exe = dist_dir / "ESP32_Lab" / "ESP32_Lab.exe"
    if output_exe.exists():
        size_mb = output_exe.stat().st_size / (1024 * 1024)
        total_size = sum(f.stat().st_size for f in (dist_dir / "ESP32_Lab").rglob("*") if f.is_file()) / (1024 * 1024)
        print("\n" + "=" * 65)
        print("[SUCCES] Compilation PyInstaller reussie !")
        print(f"   Executable : {output_exe} ({size_mb:.1f} Mo)")
        print(f"   Taille totale de distribution : {total_size:.1f} Mo")
        print("=" * 65)
    else:
        print(f"\n[AVERTISSEMENT] L'executable {output_exe} n'a pas ete trouve.")
        return

    # Compilation de l'installateur avec Inno Setup
    iss_file = root_dir / "installer.iss"
    if not iss_file.exists():
        print("[INFO] Pas de fichier installer.iss trouve.")
        return

    iscc_candidates = [
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe")),
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Users\bel-h\AppData\Local\Programs\Inno Setup 6\ISCC.exe"),
    ]
    iscc_exe = next((p for p in iscc_candidates if p.exists()), None)
    if not iscc_exe:
        iscc_path = shutil.which("ISCC")
        if iscc_path:
            iscc_exe = Path(iscc_path)

    if iscc_exe:
        print("\n" + "=" * 65)
        print(">> Generation de l'installateur Windows (Inno Setup 6)")
        print(f"   Compilateur : {iscc_exe}")
        print("=" * 65)
        res_inno = subprocess.run([str(iscc_exe), str(iss_file)], cwd=str(root_dir))
        if res_inno.returncode == 0:
            setup_file = root_dir / "dist_installer" / "ESP32_MicroPython_Lab_Setup_v2.0.exe"
            print("\n" + "=" * 65)
            print("[SUCCES] Installateur cree avec succes !")
            if setup_file.exists():
                setup_size = setup_file.stat().st_size / (1024 * 1024)
                print(f"   Fichier d'installation : {setup_file} ({setup_size:.1f} Mo)")
            print("=" * 65)
        else:
            print("\n[ERREUR] Echec de la generation de l'installateur Inno Setup.")
    else:
        print("\n[AVERTISSEMENT] Compilateur Inno Setup (ISCC.exe) non trouve sur le systeme.")


if __name__ == "__main__":
    build()
