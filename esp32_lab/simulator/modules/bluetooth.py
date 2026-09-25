"""
Module 'bluetooth' et 'ubluetooth' émulé pour l'environnement MicroPython virtuel de l'ESP32.
Permet d'exécuter des scripts BLE : advertising, services GATT, scan et notifications simulées.
"""

# Drapeaux de caractéristiques GATT standard MicroPython
FLAG_READ = 0x0002
FLAG_WRITE_NO_RESPONSE = 0x0004
FLAG_WRITE = 0x0008
FLAG_NOTIFY = 0x0010
FLAG_INDICATE = 0x0020

# Événements IRQ standard
_IRQ_CENTRAL_CONNECT = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE = 3
_IRQ_GATTS_READ_REQUEST = 4
_IRQ_SCAN_RESULT = 5
_IRQ_SCAN_DONE = 6
_IRQ_PERIPHERAL_CONNECT = 7
_IRQ_PERIPHERAL_DISCONNECT = 8
_IRQ_GATTC_SERVICE_RESULT = 9
_IRQ_GATTC_CHARACTERISTIC_RESULT = 10
_IRQ_GATTC_DESCRIPTOR_RESULT = 11
_IRQ_GATTC_READ_RESULT = 12
_IRQ_GATTC_WRITE_STATUS = 13
_IRQ_GATTC_NOTIFY = 14
_IRQ_GATTC_INDICATE = 15


class UUID:
    """Représentation d'un identifiant universel GATT 16-bit ou 128-bit."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"UUID({self.value})"

    def __repr__(self):
        return f"UUID({self.value})"


class BLE:
    """Émulateur de la couche Bluetooth Low Energy (BLE) de MicroPython."""

    def __init__(self):
        self._active = False
        self._irq_handler = None
        self._services = []
        self._handles = {}
        self._handle_counter = 1
        self._advertising = False
        self._connected = False
        self._conn_handle = 0
        self._gap_name = "ESP32-BLE"

    def active(self, is_active: bool | None = None) -> bool | None:
        """Active ou désactive la radio BLE, ou retourne l'état actuel."""
        if is_active is None:
            return self._active
        self._active = bool(is_active)
        if not self._active:
            self._advertising = False
            self._connected = False
        return None

    def irq(self, handler):
        """Définit le gestionnaire d'interruptions (callback) pour les événements BLE."""
        self._irq_handler = handler

    def gap_advertise(self, interval_us: int | None = None, adv_data: bytes | None = None, resp_data: bytes | None = None, connectable: bool = True):
        """Démarre ou arrête la diffusion publicitaire BLE (advertising)."""
        if not self._active:
            raise OSError("La radio BLE doit être activée avant l'advertising (ble.active(True))")
        if interval_us is None or interval_us == 0:
            self._advertising = False
        else:
            self._advertising = True

    def gap_scan(self, duration_ms: int, interval_us: int = 1280000, window_us: int = 11250):
        """Découvre les périphériques BLE et Bluetooth environnants (matériel hôte réel + balises)."""
        if not self._active:
            raise OSError("La radio BLE doit être activée avant le scan (ble.active(True))")
        if not self._irq_handler:
            return

        import hashlib
        import subprocess

        found_devices = []

        # Interroger les périphériques Bluetooth réels connus sur l'ordinateur
        try:
            cmd = ["powershell", "-Command", "Get-PnpDevice -Class Bluetooth | Select-Object -ExpandProperty FriendlyName"]
            res = subprocess.check_output(cmd, text=True, errors="ignore", timeout=3)
            seen = set()
            for line in res.splitlines():
                name = line.strip()
                if not name or len(name) < 2:
                    continue
                lower = name.lower()
                if any(w in lower for w in ["service", "profil", "transport", "enum", "intel", "microsoft", "generic", "rfcomm", "adaptateur"]):
                    continue
                if name not in seen:
                    seen.add(name)
                    found_devices.append((name, -60))
        except Exception:
            pass

        # Balises et périphériques BLE complémentaires réalistes
        default_beacons = [
            ("iBeacon_Salle_A", -52),
            ("Montre_Connectee_BLE", -68),
            ("Capteur_DHT_BLE", -74),
        ]
        for name, rssi in default_beacons:
            if not any(d[0] == name for d in found_devices):
                found_devices.append((name, rssi))

        # Émettre les événements _IRQ_SCAN_RESULT standard MicroPython
        for name, rssi in found_devices:
            # Générer une adresse MAC déterministe
            h = hashlib.md5(name.encode("utf-8")).digest()
            addr = bytes([0x24, 0x6F]) + h[:4]
            
            # Payload publicitaire BLE standard (Flags 0x01 + Complete Local Name 0x09)
            name_bytes = name.encode("utf-8")
            adv_data = bytes([0x02, 0x01, 0x06, len(name_bytes) + 1, 0x09]) + name_bytes
            
            # Signature: addr_type, addr, adv_type, rssi, adv_data
            self._irq_handler(_IRQ_SCAN_RESULT, (0, addr, 0, rssi, adv_data))

        # Fin du scan
        self._irq_handler(_IRQ_SCAN_DONE, ())

    def gatts_register_services(self, services):
        """Enregistre un ensemble de services et caractéristiques GATT."""
        handles = []
        for service in services:
            service_uuid, chars = service
            char_handles = []
            for char in chars:
                char_uuid, flags = char[0], char[1]
                h = self._handle_counter
                self._handle_counter += 1
                self._handles[h] = bytearray()
                char_handles.append((h,))
            handles.append(char_handles)
        return handles

    def gatts_read(self, value_handle: int) -> bytes:
        """Lit la valeur actuelle d'une caractéristique GATT enregistrée."""
        return bytes(self._handles.get(value_handle, b""))

    def gatts_write(self, value_handle: int, data: bytes) -> None:
        """Écrit une valeur dans une caractéristique GATT."""
        self._handles[value_handle] = bytearray(data)

    def gatts_notify(self, conn_handle: int, value_handle: int, data: bytes | None = None) -> None:
        """Envoie une notification d'une caractéristique à un client central connecté."""
        if data is not None:
            self.gatts_write(value_handle, data)

    def config(self, *args, **kwargs):
        """Configure ou lit les paramètres radio BLE (ex: mac, gap_name, rxbuf)."""
        if "gap_name" in kwargs:
            self._gap_name = kwargs["gap_name"]
        if args and len(args) == 1:
            param = args[0]
            if param == "mac":
                return (0, b"\x24\x6f\x28\xab\xcd\xef")
            elif param == "gap_name":
                return self._gap_name
        return None
