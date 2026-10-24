"""
Package board_profiles : Gestion des profils de cartes microcontrôleurs (ESP32, Arduino Uno, etc.)
"""

from pathlib import Path
import json
from typing import Dict

from .board_profile import BoardProfile, PinProfile, BoardPinType

DEFAULT_BOARD_ID = "esp32_wroom_32"

_PROFILES_CACHE: Dict[str, BoardProfile] = {}
_PROFILES_DIR = Path(__file__).parent


def _load_json_profile(file_path: Path) -> BoardProfile:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BoardProfile.from_dict(data)


def load_board_profile(board_id: str = DEFAULT_BOARD_ID) -> BoardProfile:
    """Charge un profil de carte par son identifiant ('esp32_wroom_32', 'arduino_uno', etc.)."""
    bid = board_id.lower().strip()
    if bid in _PROFILES_CACHE:
        return _PROFILES_CACHE[bid]

    # Alias fréquents
    aliases = {
        "esp32": "esp32_wroom_32",
        "esp32_devkit": "esp32_wroom_32",
        "esp32_devkit_v1": "esp32_wroom_32",
        "uno": "arduino_uno",
        "arduino": "arduino_uno",
    }
    canonical_id = aliases.get(bid, bid)
    if canonical_id in _PROFILES_CACHE:
        return _PROFILES_CACHE[canonical_id]

    # Recherche fichier JSON
    candidates = [
        _PROFILES_DIR / f"{canonical_id}.json",
        _PROFILES_DIR / f"{canonical_id.replace('_wroom_32', '_devkit')}.json",
    ]
    for p in candidates:
        if p.exists():
            profile = _load_json_profile(p)
            _PROFILES_CACHE[canonical_id] = profile
            _PROFILES_CACHE[profile.id] = profile
            return profile

    # Fallback par défaut ESP32 si non trouvé
    esp32_file = _PROFILES_DIR / "esp32_devkit.json"
    if esp32_file.exists():
        fallback = _load_json_profile(esp32_file)
        _PROFILES_CACHE[canonical_id] = fallback
        return fallback

    raise FileNotFoundError(f"Profil de carte introuvable pour l'identifiant: {board_id}")


def get_available_boards() -> Dict[str, BoardProfile]:
    """Retourne l'ensemble des profils de cartes disponibles."""
    for json_file in _PROFILES_DIR.glob("*.json"):
        try:
            prof = _load_json_profile(json_file)
            if prof.id not in _PROFILES_CACHE:
                _PROFILES_CACHE[prof.id] = prof
        except Exception:
            pass
    return dict(_PROFILES_CACHE)


def register_board_profile(profile: BoardProfile) -> None:
    """Enregistre dynamiquement un profil de carte en mémoire."""
    _PROFILES_CACHE[profile.id] = profile


get_board_profile = load_board_profile


__all__ = [
    "BoardProfile",
    "PinProfile",
    "BoardPinType",
    "DEFAULT_BOARD_ID",
    "load_board_profile",
    "get_board_profile",
    "get_available_boards",
    "register_board_profile",
]
