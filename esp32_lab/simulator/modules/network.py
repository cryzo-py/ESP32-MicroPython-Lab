"""
Module 'network' émulé pour l'environnement MicroPython virtuel de l'ESP32.
Permet d'exécuter des scripts IoT avec network.WLAN(STA_IF / AP_IF), connect(), isconnected(), et ifconfig().
Prend en charge le mode Passerelle Réseau Réelle (Host Network Bridge) pour utiliser
la véritable connexion IP et les interfaces sans-fil du PC hôte.
"""

import socket
import subprocess
import sys

STA_IF = 0
AP_IF = 1

# Contrôle du mode Passerelle Réseau Réelle (activé par défaut dans MainWindow via settings)
_USE_HOST_BRIDGE = False


def set_host_bridge_enabled(enabled: bool) -> None:
    """Active ou désactive la passerelle vers la carte réseau réelle du PC."""
    global _USE_HOST_BRIDGE
    _USE_HOST_BRIDGE = bool(enabled)


def is_host_bridge_enabled() -> bool:
    """Indique si la passerelle vers le réseau réel du PC est active."""
    return _USE_HOST_BRIDGE


def get_host_network_info() -> tuple[str, str, str, str]:
    """Détecte l'adresse IP et la passerelle réelles de la machine hôte."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Négocie la table de routage vers une adresse publique sans émettre de trafic
        s.connect(("8.8.8.8", 80))
        host_ip = s.getsockname()[0]
        s.close()
        parts = host_ip.split(".")
        gateway = f"{parts[0]}.{parts[1]}.{parts[2]}.1" if len(parts) == 4 else "192.168.1.1"
        return (host_ip, "255.255.255.0", gateway, "8.8.8.8")
    except Exception:
        return ("192.168.1.100", "255.255.255.0", "192.168.1.1", "8.8.8.8")


def scan_real_wifi_networks() -> list:
    """Tente d'interroger la carte Wi-Fi du PC pour lister les véritables réseaux environnants."""
    networks = []
    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True,
                timeout=2.0
            )
            if res.returncode == 0:
                raw = res.stdout.decode("cp1252", errors="replace")
                current_ssid = ""
                channel = 1
                signal_rssi = -60
                bssid = b"\xaa\xbb\xcc\xdd\xee\x01"

                for line in raw.splitlines():
                    line = line.strip()
                    if line.startswith("SSID") and ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1 and parts[1].strip():
                            current_ssid = parts[1].strip()
                    elif "Canal" in line or "Channel" in line:
                        try:
                            channel = int(line.split(":")[-1].strip())
                        except Exception:
                            channel = 6
                    elif "Signal" in line:
                        try:
                            pct = int(line.split(":")[-1].replace("%", "").strip())
                            signal_rssi = int(-100 + (pct / 100.0) * 60)
                        except Exception:
                            signal_rssi = -65
                    elif ("BSSID" in line or "Type de réseau" in line) and current_ssid:
                        networks.append((
                            current_ssid.encode("utf-8"),
                            bssid,
                            channel,
                            signal_rssi,
                            4,
                            False
                        ))
                        current_ssid = ""
        except Exception:
            pass

    # Fallback propre et réaliste si le Wi-Fi du PC est éteint ou sur câble Ethernet
    if not networks:
        networks = [
            (b"ESP32_Lab_WiFi", b"\xaa\xbb\xcc\xdd\xee\x02", 6, -52, 4, False),
            (b"Livebox-6F2A", b"\xaa\xbb\xcc\xdd\xee\x01", 1, -48, 3, False),
            (b"Freebox_Ultra_5G", b"\xaa\xbb\xcc\xdd\xee\x03", 11, -68, 4, False),
            (b"Campus_Etudiants_IoT", b"\xaa\xbb\xcc\xdd\xee\x04", 6, -75, 5, False),
        ]
    return networks


class WLAN:
    """Émulateur d'interface WiFi MicroPython (Station et Point d'Accès)."""

    def __init__(self, interface_id: int = STA_IF):
        self.interface_id = interface_id
        self._is_active = False
        self._is_connected = False
        self._ssid = ""
        
        if _USE_HOST_BRIDGE and interface_id == STA_IF:
            self._ip, self._subnet, self._gateway, self._dns = get_host_network_info()
        else:
            self._ip = "192.168.1.100" if interface_id == STA_IF else "192.168.4.1"
            self._subnet = "255.255.255.0"
            self._gateway = "192.168.1.1" if interface_id == STA_IF else "192.168.4.1"
            self._dns = "8.8.8.8"

    def active(self, is_active: bool | None = None) -> bool | None:
        """Active ou désactive l'interface radio, ou retourne son état."""
        if is_active is None:
            return self._is_active
        self._is_active = bool(is_active)
        if not self._is_active:
            self._is_connected = False
        return None

    def connect(self, ssid: str, password: str = "", bssid: bytes | None = None) -> None:
        """Simule la négociation et l'association au réseau WiFi."""
        self._ssid = str(ssid)
        if not self._is_active:
            self._is_active = True
        self._is_connected = True
        
        # Mettre à jour avec l'IP réelle si la passerelle hôte est active
        if _USE_HOST_BRIDGE and self.interface_id == STA_IF:
            self._ip, self._subnet, self._gateway, self._dns = get_host_network_info()

    def disconnect(self) -> None:
        """Déconnecte la station du point d'accès."""
        self._is_connected = False

    def isconnected(self) -> bool:
        """Indique si la liaison WiFi est établie et fonctionnelle."""
        return self._is_active and self._is_connected

    def status(self, param: str | None = None) -> int:
        """Retourne le code de statut de la connexion (1000 = STAT_GOT_IP)."""
        return 1000 if self.isconnected() else 0

    def ifconfig(self, config_tuple: tuple | None = None) -> tuple:
        """Configure ou retourne (ip, subnet, gateway, dns)."""
        if config_tuple is not None and len(config_tuple) == 4:
            self._ip, self._subnet, self._gateway, self._dns = config_tuple
        return (self._ip, self._subnet, self._gateway, self._dns)

    def scan(self) -> list:
        """Découvre les réseaux WiFi (réels si disponibles, sinon liste simulée)."""
        if _USE_HOST_BRIDGE:
            return scan_real_wifi_networks()
        return [
            (b"ESP32_Lab_WiFi", b"\xaa\xbb\xcc\xdd\xee\x02", 6, -58, 4, False),
            (b"WiFi_Maison_2.4G", b"\xaa\xbb\xcc\xdd\xee\x01", 1, -45, 3, False),
            (b"FreeWifi_Secure", b"\xaa\xbb\xcc\xdd\xee\x03", 11, -72, 3, True),
        ]

    def config(self, *args, **kwargs):
        """Permet de régler ou lire des paramètres radio comme le canal ou le mac."""
        if args and len(args) == 1:
            param = args[0]
            if param == "mac":
                return b"\x24\x6f\x28\xab\xcd\xef"
            elif param == "essid":
                return self._ssid
            elif param == "channel":
                return 1
        return None
