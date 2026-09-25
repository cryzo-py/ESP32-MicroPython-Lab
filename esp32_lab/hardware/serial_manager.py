"""
Gestionnaire de connexion série USB / COM (SerialManager) sous PySerial
"""

import threading
import time
from typing import Callable
import serial
import serial.tools.list_ports
from PySide6.QtCore import QObject, QTimer, Signal

from ..app.event_bus import get_event_bus


class SerialManager(QObject):
    ports_updated = Signal(list)
    connection_changed = Signal(bool, str) # is_connected, port_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = get_event_bus()
        self.serial_port: serial.Serial | None = None
        self.current_port_name: str = ""
        self.baudrate: int = 115200

        self._reading_thread: threading.Thread | None = None
        self._stop_reading = threading.Event()

        # Timer pour scanner automatiquement les ports toutes les 3 secondes
        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self.scan_ports)
        self._scan_timer.start(3000)

        # Écouter les données à envoyer
        self.event_bus.serial_data_to_send.connect(self.write_data)

    KNOWN_MICROCONTROLLER_VIDS = {
        0x10C4,  # Silicon Laboratories (CP2102, CP2104, CP2108, CP2105 - ESP32 DevKit standard)
        0x1A86,  # QinHeng Electronics / WCH (CH340, CH341, CH9102, CH343 - ESP32 clones standard)
        0x303A,  # Espressif Systems (ESP32-S2, ESP32-S3, ESP32-C3 native USB/JTAG)
        0x0403,  # FTDI (FT232, FT2232, FT4232)
        0x2341,  # Arduino LLC
        0x2E8A,  # Raspberry Pi Foundation (RP2040 / Pico)
        0x067B,  # Prolific Technology (PL2303)
        0x1366,  # SEGGER (J-Link)
    }

    KNOWN_BOARD_KEYWORDS = (
        "cp210", "ch340", "ch341", "ch9102", "ch343",
        "esp32", "espressif", "ft232", "ftdi",
        "silicon labs", "silicon laboratories",
        "nodemcu", "wroom", "devkit",
    )

    IGNORED_VIDS = {
        0x8087,  # Intel Bluetooth / Wireless virtual COM
    }

    def scan_ports(self) -> list[tuple[str, str]]:
        """Détecte les ports série USB disponibles et la présence matérielle d'une carte microcontrôleur."""
        ports = []
        matching_boards = []
        try:
            for p in serial.tools.list_ports.comports():
                desc = p.description or ""
                ports.append((p.device, desc))

                vid = getattr(p, "vid", None)
                if vid in self.IGNORED_VIDS:
                    continue

                desc_lower = desc.lower()
                mfg_lower = (getattr(p, "manufacturer", None) or "").lower()
                hwid_lower = (getattr(p, "hwid", None) or "").lower()

                is_known_vid = vid in self.KNOWN_MICROCONTROLLER_VIDS
                is_known_kw = any(k in desc_lower or k in mfg_lower or k in hwid_lower for k in self.KNOWN_BOARD_KEYWORDS)

                if is_known_vid or is_known_kw:
                    matching_boards.append((p.device, desc))
        except Exception:
            pass

        self.ports_updated.emit(ports)
        self.event_bus.device_detection_updated.emit(ports)

        # Si un port était connecté mais a disparu physiquement (débranchement USB)
        if self.current_port_name and not any(p[0] == self.current_port_name for p in ports):
            self.disconnect_port()

        # Présence réelle : soit l'utilisateur est connecté dans l'app, soit une carte physique réelle est détectée
        is_present = self.is_connected() or (len(matching_boards) > 0)
        detected_name = self.current_port_name or (matching_boards[0][0] if matching_boards else "")
        self.event_bus.usb_hardware_detected.emit(is_present, detected_name)

        return ports

    def connect_port(self, port_name: str, baudrate: int = 115200) -> bool:
        self.disconnect_port()
        if not port_name:
            return False

        try:
            self.serial_port = serial.Serial(port_name, baudrate=baudrate, timeout=0.1)
            self.current_port_name = port_name
            self.baudrate = baudrate

            # Démarrer le thread de lecture
            self._stop_reading.clear()
            self._reading_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reading_thread.start()

            self.connection_changed.emit(True, port_name)
            self.event_bus.device_connected.emit(port_name)
            self.event_bus.usb_hardware_detected.emit(True, port_name)
            self.event_bus.serial_data_received.emit(f"\n>>> Connecté à {port_name} ({baudrate} bauds)\n")
            return True
        except Exception as ex:
            self.event_bus.serial_data_received.emit(f"\n❌ Erreur de connexion série ({port_name}): {ex}\n")
            return False

    def disconnect_port(self):
        if self.serial_port and self.serial_port.is_open:
            self._stop_reading.set()
            if self._reading_thread and self._reading_thread.is_alive():
                self._reading_thread.join(timeout=0.5)
            try:
                self.serial_port.close()
            except Exception:
                pass
            self.serial_port = None
            old_port = self.current_port_name
            self.current_port_name = ""
            self.connection_changed.emit(False, "")
            self.event_bus.device_disconnected.emit()
            self.event_bus.usb_hardware_detected.emit(False, "")
            if old_port:
                self.event_bus.serial_data_received.emit(f"\n>>> Déconnecté de {old_port}\n")

    def is_connected(self) -> bool:
        return self.serial_port is not None and self.serial_port.is_open

    def write_data(self, data: str):
        if self.is_connected() and self.serial_port:
            try:
                if not data.endswith("\r\n") and not data.endswith("\n"):
                    data += "\r\n"
                self.serial_port.write(data.encode("utf-8"))
            except Exception as ex:
                self.event_bus.serial_data_received.emit(f"\n❌ Erreur écriture série: {ex}\n")

    def write_bytes(self, data: bytes):
        if self.is_connected() and self.serial_port:
            self.serial_port.write(data)

    def _read_loop(self):
        while not self._stop_reading.is_set():
            if self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting:
                        chunk = self.serial_port.read(self.serial_port.in_waiting)
                        if chunk:
                            text = chunk.decode("utf-8", errors="replace")
                            self.event_bus.serial_data_received.emit(text)
                            self.event_bus.repl_data_received.emit(text)
                except Exception:
                    # Déconnexion inattendue (câble arraché du PC)
                    QTimer.singleShot(0, self.disconnect_port)
                    break
            time.sleep(0.02)
