"""
Module de vérification et notification des mises à jour via GitHub Releases.
Dépôt officiel : https://github.com/cryzo-py/ESP32-MicroPython-Lab
"""

import json
import re
import urllib.error
import urllib.request
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QThread, Signal
from esp32_lab import __version__

GITHUB_REPO = "cryzo-py/ESP32-MicroPython-Lab"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"


def parse_version(v_str: str) -> Tuple[int, ...]:
    """Extrait un tuple d'entiers normalisé (ex: 'v2.0' -> (2, 0, 0)) pour comparaison."""
    cleaned = re.sub(r"^[^\d]*", "", str(v_str).strip())
    nums = [int(n) for n in re.findall(r"\d+", cleaned)]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums) if nums else (0, 0, 0)


def is_newer_version(latest_str: str, current_str: str = __version__) -> bool:
    """Compare la version distante à la version courante."""
    return parse_version(latest_str) > parse_version(current_str)


class UpdateCheckerThread(QThread):
    """
    Thread asynchrone non-bloquant interrogeant l'API GitHub Releases.
    Émet les signaux 'check_finished' ou 'check_failed'.
    """
    check_finished = Signal(dict)
    check_failed = Signal(str)

    def __init__(self, parent=None, current_version: str = __version__):
        super().__init__(parent)
        self.current_version = current_version

    def run(self):
        headers = {
            "User-Agent": f"ESP32-MicroPython-Lab/{self.current_version}",
            "Accept": "application/vnd.github.v3+json",
        }
        req = urllib.request.Request(API_URL, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                html_url = data.get("html_url", RELEASES_URL)
                body = data.get("body", "")

                assets = data.get("assets", [])
                exe_download_url = html_url
                for asset in assets:
                    name = asset.get("name", "").lower()
                    if name.endswith(".exe") or "setup" in name:
                        exe_download_url = asset.get("browser_download_url", html_url)
                        break

                has_update = is_newer_version(tag_name, self.current_version)
                result = {
                    "has_update": has_update,
                    "latest_version": tag_name,
                    "current_version": self.current_version,
                    "html_url": html_url,
                    "download_url": exe_download_url,
                    "release_notes": body,
                }
                self.check_finished.emit(result)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.check_finished.emit({
                    "has_update": False,
                    "latest_version": self.current_version,
                    "current_version": self.current_version,
                    "html_url": RELEASES_URL,
                    "download_url": RELEASES_URL,
                    "release_notes": "Aucune release distante trouvée pour le moment.",
                    "not_found": True,
                })
            else:
                self.check_failed.emit(f"Erreur HTTP {e.code} : {e.reason}")
        except urllib.error.URLError:
            self.check_failed.emit("Impossible de contacter GitHub. Vérifiez votre connexion Internet.")
        except Exception as e:
            self.check_failed.emit(f"Erreur imprévue : {str(e)}")
