"""
Service de compilation et téléversement vers carte Arduino physique via arduino-cli
"""

import logging
import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from ..app.event_bus import get_event_bus

logger = logging.getLogger(__name__)


class ArduinoCLIUploader(QObject):
    upload_started = Signal()
    upload_progress = Signal(int, str)
    upload_finished = Signal(bool, str)

    DEFAULT_FQBN = "arduino:avr:uno"

    def __init__(self, serial_manager, parent=None):
        super().__init__(parent)
        self.serial_manager = serial_manager
        self.event_bus = get_event_bus()

    @staticmethod
    def find_arduino_cli() -> str | None:
        """Recherche l'exécutable arduino-cli dans le PATH et les répertoires standards."""
        # 1. Vérifier si accessible directement dans le PATH
        cli = shutil.which("arduino-cli") or shutil.which("arduino-cli.exe")
        if cli:
            return cli

        # 2. Chemins standards sous Windows
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Arduino15" / "bin" / "arduino-cli.exe",
            Path(os.environ.get("ProgramFiles", "")) / "Arduino CLI" / "arduino-cli.exe",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Arduino CLI" / "arduino-cli.exe",
            Path(os.environ.get("USERPROFILE", "")) / "bin" / "arduino-cli.exe",
            Path(os.environ.get("USERPROFILE", "")) / "arduino-cli.exe",
            Path("C:/arduino-cli/arduino-cli.exe"),
        ]
        for p in candidates:
            if p.is_file():
                return str(p)

        return None

    def is_available(self) -> bool:
        """Vérifie si arduino-cli est installé et accessible."""
        return self.find_arduino_cli() is not None

    def get_version(self) -> str | None:
        """Retourne la version installée d'arduino-cli."""
        cli = self.find_arduino_cli()
        if not cli:
            return None
        try:
            res = subprocess.run([cli, "version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception as e:
            logger.warning("Erreur vérification version arduino-cli: %s", e)
        return None

    def upload_code(self, code: str, fqbn: str = DEFAULT_FQBN, port: str = None):
        """Lance la compilation et le téléversement dans un thread d'arrière-plan."""
        target_port = port or self.serial_manager.current_port_name
        if not target_port:
            self.event_bus.upload_finished.emit(False, "Aucun port COM sélectionné")
            self.event_bus.serial_data_received.emit(
                "\n❌ Téléversement impossible : aucune carte Arduino connectée sur un port COM.\n"
            )
            return

        thread = threading.Thread(
            target=self._do_compile_and_upload,
            args=(code, target_port, fqbn),
            daemon=True
        )
        thread.start()

    def _do_compile_and_upload(self, code: str, port: str, fqbn: str):
        self.upload_started.emit()
        self.event_bus.upload_started.emit()

        cli = self.find_arduino_cli()
        if not cli:
            err_msg = (
                "\n❌ Outil 'arduino-cli' introuvable sur votre ordinateur.\n\n"
                "Pour téléverser un programme C/C++ sur votre carte Arduino physique :\n"
                "1. Téléchargez arduino-cli : https://arduino.github.io/arduino-cli/\n"
                "   Ou installez-le avec winget : winget install ArduinoSA.CLI\n"
                "2. Installez le cœur AVR : arduino-cli core install arduino:avr\n"
                "3. Relancez ESP32 Lab.\n"
            )
            self.event_bus.serial_data_received.emit(err_msg)
            self.upload_finished.emit(False, "arduino-cli introuvable")
            self.event_bus.upload_finished.emit(False, "arduino-cli introuvable")
            return

        temp_dir = None
        was_connected = False
        try:
            self.upload_progress.emit(10, "Préparation du fichier sketch...")
            self.event_bus.upload_progress.emit(10, "Préparation du fichier sketch...")

            # Créer un répertoire temporaire nommé selon la convention Arduino:
            # {dossier}/{dossier}.ino
            temp_dir = tempfile.mkdtemp(prefix="esp32lab_arduino_")
            sketch_name = "esp32lab_sketch"
            sketch_folder = Path(temp_dir) / sketch_name
            sketch_folder.mkdir(parents=True, exist_ok=True)
            sketch_file = sketch_folder / f"{sketch_name}.ino"

            with open(sketch_file, "w", encoding="utf-8") as f:
                f.write(code)

            self.event_bus.serial_data_received.emit(
                f"\n⚙️ [COMPILATION ARDUINO] Cible : {fqbn}\n"
            )
            self.upload_progress.emit(30, "Compilation du croquis C++...")
            self.event_bus.upload_progress.emit(30, "Compilation du croquis C++...")

            # Exécuter la compilation
            compile_cmd = [
                cli, "compile",
                "--fqbn", fqbn,
                str(sketch_folder)
            ]
            comp_proc = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )

            if comp_proc.stdout:
                self.event_bus.serial_data_received.emit(comp_proc.stdout)
            if comp_proc.stderr:
                self.event_bus.serial_data_received.emit(comp_proc.stderr)

            if comp_proc.returncode != 0:
                self.event_bus.serial_data_received.emit(
                    "\n❌ Échec de la compilation C++ du croquis Arduino.\n"
                )
                self.upload_finished.emit(False, "Erreur de compilation")
                self.event_bus.upload_finished.emit(False, "Erreur de compilation")
                return

            self.upload_progress.emit(65, "Compilation réussie ! Libération du port COM...")
            self.event_bus.upload_progress.emit(65, "Compilation réussie ! Libération du port COM...")

            # Fermer temporairement le port série dans SerialManager pour libérer l'accès USB à avrdude
            if self.serial_manager and self.serial_manager.is_connected():
                was_connected = True
                self.serial_manager.disconnect_port()
                time.sleep(0.3)

            self.upload_progress.emit(75, f"Téléversement vers {port}...")
            self.event_bus.upload_progress.emit(75, f"Téléversement vers {port}...")
            self.event_bus.serial_data_received.emit(
                f"🚀 [TÉLÉVERSEMENT] Envoi vers {port}...\n"
            )

            # Exécuter le téléversement
            upload_cmd = [
                cli, "upload",
                "-p", port,
                "--fqbn", fqbn,
                str(sketch_folder)
            ]
            up_proc = subprocess.run(
                upload_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )

            if up_proc.stdout:
                self.event_bus.serial_data_received.emit(up_proc.stdout)
            if up_proc.stderr:
                self.event_bus.serial_data_received.emit(up_proc.stderr)

            if up_proc.returncode != 0:
                self.event_bus.serial_data_received.emit(
                    f"\n❌ Échec du téléversement vers {port}.\n"
                )
                self.upload_finished.emit(False, "Erreur de téléversement")
                self.event_bus.upload_finished.emit(False, "Erreur de téléversement")
                return

            self.upload_progress.emit(100, "Téléversement terminé avec succès !")
            self.event_bus.upload_progress.emit(100, "Téléversement terminé avec succès !")
            self.upload_finished.emit(True, "Téléversement réussi !")
            self.event_bus.upload_finished.emit(True, "Téléversement réussi !")
            self.event_bus.serial_data_received.emit(
                f"\n✔ [SUCCÈS] Programme téléversé avec succès sur la carte Arduino ({port}) !\n"
            )

        except subprocess.TimeoutExpired:
            self.event_bus.serial_data_received.emit("\n❌ Délai d'attente dépassé (timeout).\n")
            self.upload_finished.emit(False, "Timeout")
            self.event_bus.upload_finished.emit(False, "Timeout")
        except Exception as ex:
            logger.exception("Erreur lors du téléversement Arduino")
            self.event_bus.serial_data_received.emit(f"\n❌ Erreur inattendue : {ex}\n")
            self.upload_finished.emit(False, str(ex))
            self.event_bus.upload_finished.emit(False, str(ex))
        finally:
            # Nettoyer les fichiers temporaires
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            # Reconnecter le port série si nécessaire
            if was_connected and self.serial_manager:
                time.sleep(0.5)
                self.serial_manager.connect_port(port)


class ArduinoLibraryService:
    """Service de gestion des bibliothèques et cœurs matériels Arduino via arduino-cli."""

    CURATED_LIBRARIES = [
        {
            "name": "Servo",
            "header": "<Servo.h>",
            "category": "Actionneurs",
            "author": "Michael Margolis, Arduino",
            "sentence": "Contrôle des servomoteurs RC (SG90, MG996R) avec gestion précise des angles de 0° à 180°.",
            "popularity": 100,
        },
        {
            "name": "LiquidCrystal",
            "header": "<LiquidCrystal.h>",
            "category": "Affichage",
            "author": "Arduino",
            "sentence": "Pilotage des afficheurs LCD alphanumériques 16x2 et 20x4 avec interface parallèle 4/8 bits.",
            "popularity": 95,
        },
        {
            "name": "LiquidCrystal I2C",
            "header": "<LiquidCrystal_I2C.h>",
            "category": "Affichage",
            "author": "Frank de Brabander / Marco Schwartz",
            "sentence": "Contrôle d'écrans LCD 1602/2004 via adaptateur I2C PCF8574 (2 broches SDA/SCL).",
            "popularity": 92,
        },
        {
            "name": "DHT sensor library",
            "header": "<DHT.h>",
            "category": "Capteurs",
            "author": "Adafruit",
            "sentence": "Lecture de température et d'humidité relative pour capteurs DHT11, DHT22 et AM2302.",
            "popularity": 90,
        },
        {
            "name": "Adafruit NeoPixel",
            "header": "<Adafruit_NeoPixel.h>",
            "category": "Affichage",
            "author": "Adafruit",
            "sentence": "Gestion des rubans, anneaux et matrices de LEDs adressables intelligentes WS2812 / WS2812B.",
            "popularity": 88,
        },
        {
            "name": "Adafruit SSD1306",
            "header": "<Adafruit_SSD1306.h>",
            "category": "Affichage",
            "author": "Adafruit",
            "sentence": "Affichage graphique monochrome pour écrans OLED 128x64 et 128x32 en bus I2C ou SPI.",
            "popularity": 85,
        },
        {
            "name": "Adafruit GFX Library",
            "header": "<Adafruit_GFX.h>",
            "category": "Graphisme",
            "author": "Adafruit",
            "sentence": "Bibliothèque graphique fondamentale (lignes, cercles, rectangles, polices) pour écrans.",
            "popularity": 85,
        },
        {
            "name": "HCSR04",
            "header": "<HCSR04.h>",
            "category": "Capteurs",
            "author": "Martin Sosic",
            "sentence": "Calcul de distance en centimètres par ultrasons via capteurs HC-SR04 et HY-SRF05.",
            "popularity": 80,
        },
        {
            "name": "Stepper",
            "header": "<Stepper.h>",
            "category": "Moteurs",
            "author": "Arduino",
            "sentence": "Pilotage pas-à-pas unipolaire ou bipolaire (moteurs 28BYJ-48 avec driver ULN2003).",
            "popularity": 78,
        },
        {
            "name": "Wire",
            "header": "<Wire.h>",
            "category": "Communication",
            "author": "Arduino (Core)",
            "sentence": "Communication sur bus série I2C / TWI (maître et esclave). Déjà incluse dans le cœur AVR.",
            "popularity": 75,
            "is_builtin": True,
        },
        {
            "name": "SPI",
            "header": "<SPI.h>",
            "category": "Communication",
            "author": "Arduino (Core)",
            "sentence": "Communication bus série synchrone haute vitesse SPI. Déjà incluse dans le cœur AVR.",
            "popularity": 75,
            "is_builtin": True,
        },
    ]

    @classmethod
    def get_cli_path(cls) -> str | None:
        return ArduinoCLIUploader.find_arduino_cli()

    @classmethod
    def is_cli_installed(cls) -> bool:
        return cls.get_cli_path() is not None

    @classmethod
    def get_cli_version(cls) -> str | None:
        cli = cls.get_cli_path()
        if not cli:
            return None
        try:
            res = subprocess.run([cli, "version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    @classmethod
    def is_avr_core_installed(cls) -> bool:
        cli = cls.get_cli_path()
        if not cli:
            return False
        try:
            res = subprocess.run([cli, "core", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
            if res.returncode == 0 and "arduino:avr" in res.stdout.lower():
                return True
        except Exception:
            pass
        return False

    @classmethod
    def list_installed_libraries(cls) -> list[dict]:
        cli = cls.get_cli_path()
        if not cli:
            return []
        try:
            import json
            res = subprocess.run([cli, "lib", "list", "--format", "json"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                libs = []
                raw_list = data.get("installed_libraries", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                for item in raw_list:
                    lib_info = item.get("library", item)
                    libs.append({
                        "name": lib_info.get("name", "Inconnu"),
                        "version": lib_info.get("version", ""),
                        "author": lib_info.get("author", ""),
                        "sentence": lib_info.get("sentence", lib_info.get("paragraph", "")),
                        "installed": True
                    })
                return libs
        except Exception as e:
            logger.warning("Erreur listage bibliothèques: %s", e)
        return []

    @classmethod
    def search_libraries(cls, query: str) -> list[dict]:
        cli = cls.get_cli_path()
        if not cli:
            return []
        try:
            import json
            res = subprocess.run([cli, "lib", "search", query, "--format", "json"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                results = []
                raw_list = data.get("libraries", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                installed_names = {l["name"].lower() for l in cls.list_installed_libraries()}
                for item in raw_list[:30]:
                    name = item.get("name", "")
                    latest = item.get("latest", {})
                    results.append({
                        "name": name,
                        "version": latest.get("version", ""),
                        "author": latest.get("author", ""),
                        "sentence": latest.get("sentence", ""),
                        "installed": name.lower() in installed_names
                    })
                return results
        except Exception as e:
            logger.warning("Erreur recherche bibliothèques: %s", e)
        return []

    @classmethod
    def install_library(cls, lib_name: str, log_callback=None) -> tuple[bool, str]:
        cli = cls.get_cli_path()
        if not cli:
            return False, "arduino-cli introuvable"
        try:
            if log_callback:
                log_callback(f"📦 Téléchargement et installation de '{lib_name}'...")
            proc = subprocess.Popen(
                [cli, "lib", "install", lib_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                universal_newlines=True
            )
            output = []
            if proc.stdout:
                for line in proc.stdout:
                    output.append(line)
                    if log_callback:
                        log_callback(line.strip())
            proc.wait(timeout=120)
            full_out = "".join(output)
            return (proc.returncode == 0, full_out)
        except Exception as e:
            return False, str(e)

    @classmethod
    def uninstall_library(cls, lib_name: str, log_callback=None) -> tuple[bool, str]:
        cli = cls.get_cli_path()
        if not cli:
            return False, "arduino-cli introuvable"
        try:
            if log_callback:
                log_callback(f"🗑️ Désinstallation de '{lib_name}'...")
            res = subprocess.run([cli, "lib", "uninstall", lib_name], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            if log_callback:
                log_callback(res.stdout or res.stderr)
            return (res.returncode == 0, res.stdout or res.stderr)
        except Exception as e:
            return False, str(e)

    @classmethod
    def install_avr_core(cls, log_callback=None) -> tuple[bool, str]:
        cli = cls.get_cli_path()
        if not cli:
            return False, "arduino-cli introuvable"
        try:
            if log_callback:
                log_callback("🔄 Mise à jour des index Arduino (core update-index)...")
            try:
                proc_idx = subprocess.Popen(
                    [cli, "core", "update-index"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    universal_newlines=True
                )
                if proc_idx.stdout:
                    for line in proc_idx.stdout:
                        if log_callback:
                            log_callback(line.strip())
                proc_idx.wait(timeout=120)
            except Exception as e:
                logger.warning("Échec mise à jour index Arduino: %s", e)

            if log_callback:
                log_callback("⚡ Installation du cœur Arduino AVR (arduino:avr) pour Uno/Nano...")
            proc = subprocess.Popen(
                [cli, "core", "install", "arduino:avr"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                universal_newlines=True
            )
            output = []
            if proc.stdout:
                for line in proc.stdout:
                    output.append(line)
                    if log_callback:
                        log_callback(line.strip())
            proc.wait(timeout=300)
            full_out = "".join(output)
            return (proc.returncode == 0, full_out)
        except Exception as e:
            return False, str(e)

    @classmethod
    def install_cli_direct(cls, log_callback=None) -> tuple[bool, str]:
        """Télécharge directement la version officielle autonome Windows d'arduino-cli depuis GitHub."""
        import io
        import json
        import urllib.request
        import zipfile

        try:
            target_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Arduino15" / "bin"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_exe = target_dir / "arduino-cli.exe"

            if log_callback:
                log_callback("🔍 Détection de la dernière version stable d'arduino-cli sur GitHub...")

            download_url = None
            try:
                api_url = "https://api.github.com/repos/arduino/arduino-cli/releases/latest"
                req = urllib.request.Request(api_url, headers={"User-Agent": "ESP32Lab-App"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for a in data.get("assets", []):
                        if "Windows_64bit.zip" in a.get("name", ""):
                            download_url = a.get("browser_download_url")
                            break
            except Exception as e:
                logger.warning("Erreur consultation API GitHub pour arduino-cli: %s", e)

            if not download_url:
                download_url = "https://github.com/arduino/arduino-cli/releases/download/v1.5.1/arduino-cli_1.5.1_Windows_64bit.zip"

            if log_callback:
                log_callback(f"⬇️ Téléchargement depuis GitHub ({download_url})...")

            req_dl = urllib.request.Request(download_url, headers={"User-Agent": "ESP32Lab-App"})
            with urllib.request.urlopen(req_dl, timeout=90) as resp:
                total_size = int(resp.headers.get("content-length", 0))
                downloaded = 0
                chunks = []
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and log_callback and downloaded % (1024 * 1024) == 0:
                        pct = int((downloaded / total_size) * 100)
                        log_callback(f"⬇️ Téléchargement en cours : {downloaded // (1024 * 1024)} Mo / {total_size // (1024 * 1024)} Mo ({pct}%)")

            zip_bytes = b"".join(chunks)
            if log_callback:
                log_callback("📦 Extraction de l'exécutable arduino-cli.exe...")

            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                found = False
                for name in z.namelist():
                    if name.lower().endswith("arduino-cli.exe"):
                        with open(target_exe, "wb") as f_out:
                            f_out.write(z.read(name))
                        found = True
                        break

            if not found or not target_exe.is_file():
                return False, "Exécutable arduino-cli.exe non trouvé dans l'archive téléchargée"

            if log_callback:
                log_callback(f"✔ arduino-cli installé avec succès dans : {target_exe}")

            # Initialisation de base
            try:
                subprocess.run([str(target_exe), "version"], capture_output=True, timeout=5)
            except Exception:
                pass

            return True, f"arduino-cli installé avec succès dans {target_dir}"
        except Exception as e:
            logger.error("Échec installation directe arduino-cli: %s", e)
            return False, str(e)

    @classmethod
    def install_cli_via_winget(cls, log_callback=None) -> tuple[bool, str]:
        try:
            if log_callback:
                log_callback("🚀 Démarrage de l'installation de arduino-cli via winget (ArduinoSA.CLI)...")
            cmd = [
                "winget", "install",
                "--id", "ArduinoSA.CLI",
                "-e", "--silent",
                "--accept-source-agreements",
                "--accept-package-agreements"
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                universal_newlines=True
            )
            output = []
            if proc.stdout:
                for line in proc.stdout:
                    output.append(line)
                    if log_callback:
                        log_callback(line.strip())
            proc.wait(timeout=300)
            full_out = "".join(output)
            if proc.returncode == 0:
                return (True, full_out)
            if log_callback:
                log_callback("⚠️ Winget a rencontré un problème. Basculement automatique sur le téléchargement autonome...")
            return cls.install_cli_direct(log_callback=log_callback)
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Winget indisponible ({e}). Basculement sur le téléchargement direct...")
            return cls.install_cli_direct(log_callback=log_callback)
