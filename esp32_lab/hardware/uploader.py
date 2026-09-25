"""
Service de téléversement vers l'ESP32 physique (Uploader via Raw REPL MicroPython)

Protocole Raw REPL :
  1. Ctrl+C x2  → interrompt tout programme en cours
  2. Ctrl+A     → entre en Raw REPL (la carte répond "raw REPL; CTRL-B to exit\r\n>")
  3. Envoi du script Python terminé par Ctrl+D
  4. La carte répond "OK" puis exécute, puis envoie "\x04\x04>" quand c'est fini
  5. Ctrl+B     → quitte le Raw REPL et déclenche un soft reboot
"""

import logging
import threading
import time
import serial
from PySide6.QtCore import QObject, Signal

from ..app.event_bus import get_event_bus

logger = logging.getLogger(__name__)


class ESP32Uploader(QObject):
    upload_started = Signal()
    upload_progress = Signal(int, str)
    upload_finished = Signal(bool, str)

    def __init__(self, serial_manager, parent=None):
        super().__init__(parent)
        self.serial_manager = serial_manager
        self.event_bus = get_event_bus()

    def upload_code(self, code: str, filename: str = "main.py"):
        """Lance le téléversement dans un thread d'arrière-plan"""
        port = self.serial_manager.current_port_name
        if not port:
            self.event_bus.upload_finished.emit(False, "Aucun port COM sélectionné")
            self.event_bus.serial_data_received.emit(
                "\n❌ Téléversement impossible : aucune ESP32 connectée.\n"
            )
            return

        thread = threading.Thread(
            target=self._do_upload, args=(port, code, filename), daemon=True
        )
        thread.start()

    # ------------------------------------------------------------------
    # Helpers pour le protocole Raw REPL
    # ------------------------------------------------------------------

    @staticmethod
    def _read_until(ser: serial.Serial, marker: bytes, timeout: float = 5.0) -> bytes:
        """Lit depuis le port série jusqu'à trouver *marker* ou dépasser *timeout*.
        Retourne tout ce qui a été lu (marker inclus si trouvé)."""
        buf = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            n = ser.in_waiting
            if n:
                buf += ser.read(n)
                if marker in buf:
                    return buf
            else:
                time.sleep(0.01)
        return buf

    @staticmethod
    def _enter_raw_repl(ser: serial.Serial) -> bool:
        """Interrompt le programme en cours et entre en mode Raw REPL.
        Retourne True si le prompt '>' a bien été reçu.
        Fait plusieurs tentatives pour gérer les boucles while True."""
        # Tentative d'interruption agressive : envoyer Ctrl+C plusieurs
        # fois avec des pauses, car une boucle while True avec sleep()
        # ne peut être interrompue que pendant l'exécution Python
        for attempt in range(3):
            ser.write(b"\r\x03\x03")
            time.sleep(0.5)

        # Vider tout ce que la carte a renvoyé (traceback, prompt, etc.)
        time.sleep(0.3)
        ser.reset_input_buffer()

        # Essayer d'entrer en Raw REPL (2 tentatives)
        for attempt in range(2):
            ser.write(b"\r\x01")
            resp = ESP32Uploader._read_until(ser, b">", timeout=3.0)
            logger.debug("enter_raw_repl attempt %d resp: %r", attempt, resp)
            if b">" in resp:
                return True
            # Deuxième tentative : re-interrompre et réessayer
            ser.write(b"\r\x03\x03")
            time.sleep(0.5)
            ser.reset_input_buffer()

        return False

    @staticmethod
    def _exec_raw(ser: serial.Serial, script: str, timeout: float = 10.0) -> tuple[bool, str]:
        """Exécute un script en Raw REPL.
        Envoie le script par petits paquets, puis Ctrl+D pour exécuter.
        Attend la réponse 'OK...\x04...\x04>' de la carte.
        Retourne (success, output_or_error)."""
        data = script.encode("utf-8")

        # Envoi par petits paquets de 128 octets avec micro-pause
        # pour ne pas déborder le buffer UART de la carte
        chunk_size = 128
        for i in range(0, len(data), chunk_size):
            ser.write(data[i : i + chunk_size])
            time.sleep(0.02)

        # Ctrl+D = fin du script, lancer l'exécution
        ser.write(b"\x04")

        # Lire la réponse : le Raw REPL envoie "OK" suivi de la sortie stdout,
        # puis \x04, puis stderr, puis \x04>
        resp = ESP32Uploader._read_until(ser, b"\x04>", timeout=timeout)
        logger.debug("exec_raw resp: %r", resp)

        if b"OK" not in resp:
            return False, resp.decode("utf-8", errors="replace")

        # Extraire stdout et stderr entre les marqueurs
        # Format : OK<stdout>\x04<stderr>\x04>
        after_ok = resp.split(b"OK", 1)[1] if b"OK" in resp else resp
        parts = after_ok.split(b"\x04")
        stdout_part = parts[0].decode("utf-8", errors="replace").strip() if len(parts) > 0 else ""
        stderr_part = parts[1].decode("utf-8", errors="replace").strip() if len(parts) > 1 else ""

        if stderr_part:
            return False, stderr_part

        return True, stdout_part

    @staticmethod
    def _exit_raw_repl(ser: serial.Serial):
        """Quitte le Raw REPL (Ctrl+B) → soft reboot."""
        ser.write(b"\r\x02")
        time.sleep(0.5)

    # ------------------------------------------------------------------
    # Upload principal
    # ------------------------------------------------------------------

    def _do_upload(self, port: str, code: str, filename: str):
        self.event_bus.upload_started.emit()
        self.event_bus.upload_progress.emit(10, "Préparation de la connexion...")

        # Fermer temporairement la lecture du SerialManager
        was_connected = self.serial_manager.is_connected()
        if was_connected:
            self.serial_manager.disconnect_port()

        time.sleep(0.3)

        ser = None
        try:
            ser = serial.Serial(port, baudrate=115200, timeout=1.0)
            time.sleep(0.1)

            # --- Étape 1 : Entrer en Raw REPL ---
            self.event_bus.upload_progress.emit(20, "Interruption du programme existant...")
            if not self._enter_raw_repl(ser):
                raise RuntimeError(
                    "Impossible d'entrer en mode Raw REPL. "
                    "Vérifiez que MicroPython est installé sur la carte."
                )

            # --- Étape 2 : Supprimer l'ancien fichier (ignorer si absent) ---
            self.event_bus.upload_progress.emit(40, f"Suppression de l'ancien {filename}...")
            delete_script = f"import os\ntry:\n    os.remove('{filename}')\nexcept:\n    pass"
            self._exec_raw(ser, delete_script, timeout=5.0)

            # Après chaque exec_raw, le prompt '>' est déjà en place
            # pour la commande suivante

            # --- Étape 3 : Écrire le nouveau fichier ---
            self.event_bus.upload_progress.emit(60, f"Écriture de {filename}...")

            # Nettoyer le code : supprimer un éventuel BOM UTF-8 et
            # normaliser les fins de ligne
            clean_code = code.lstrip("\ufeff").replace("\r\n", "\n")
            escaped_code = repr(clean_code)
            write_script = f"with open('{filename}', 'w') as _f:\n    _f.write({escaped_code})"

            ok, output = self._exec_raw(ser, write_script, timeout=10.0)
            if not ok:
                raise RuntimeError(
                    f"Erreur lors de l'écriture de {filename} sur la carte : {output}"
                )

            # --- Étape 4 : Vérifier que le fichier existe et a la bonne taille ---
            self.event_bus.upload_progress.emit(80, "Vérification...")
            verify_script = f"import os; print(os.stat('{filename}')[6])"
            ok, size_str = self._exec_raw(ser, verify_script, timeout=5.0)
            if ok and size_str.strip().isdigit():
                written_size = int(size_str.strip())
                expected_size = len(clean_code.encode("utf-8"))
                if written_size != expected_size:
                    logger.warning(
                        "Taille fichier inattendue : %d vs %d attendu",
                        written_size, expected_size,
                    )

            # --- Étape 5 : Sortir du Raw REPL (soft reboot → exécute main.py) ---
            self.event_bus.upload_progress.emit(90, "Redémarrage de l'ESP32...")
            self._exit_raw_repl(ser)

            self.event_bus.upload_progress.emit(100, "Terminé !")
            self.event_bus.upload_finished.emit(True, f"{filename} téléversé avec succès !")
            self.event_bus.serial_data_received.emit(
                f"\n✔ [TÉLÉVERSEMENT RÉUSSI] Le code a été transféré sur {port} et s'exécute.\n"
            )

        except Exception as ex:
            logger.exception("Erreur téléversement")
            self.event_bus.upload_finished.emit(False, str(ex))
            self.event_bus.serial_data_received.emit(
                f"\n❌ Erreur lors du téléversement vers {port}: {ex}\n"
            )
        finally:
            # Toujours fermer le port série pour ne pas bloquer la reconnexion
            if ser is not None and ser.is_open:
                try:
                    ser.close()
                except Exception:
                    pass
            # Rétablir la connexion série normale
            if was_connected:
                time.sleep(0.5)
                self.serial_manager.connect_port(port)

