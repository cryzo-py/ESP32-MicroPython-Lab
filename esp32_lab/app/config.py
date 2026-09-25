"""
Configuration de l'application ESP32 MicroPython Lab
"""

from dataclasses import dataclass, field
import json
import os
from pathlib import Path


@dataclass
class AppConfig:
    theme: str = "dark"
    font_size: int = 14
    tab_size: int = 4
    autosave_enabled: bool = True
    autosave_delay_ms: int = 1500
    default_baudrate: int = 115200
    last_port: str = ""
    recent_projects: list[str] = field(default_factory=list)

    @classmethod
    def get_config_path(cls) -> Path:
        app_dir = Path.home() / ".esp32_lab"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir / "config.json"

    @classmethod
    def load(cls) -> "AppConfig":
        config_path = cls.get_config_path()
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**data)
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        config_path = self.get_config_path()
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, indent=2)
        except Exception:
            pass
