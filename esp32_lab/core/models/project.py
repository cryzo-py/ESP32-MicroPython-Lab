"""
Modèle représentant un projet ESP32 MicroPython Lab
"""

from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .component import ComponentModel
from .connection import ConnectionModel


DEFAULT_MAIN_PY = """# Exemple : LED clignotante sur ESP32
from machine import Pin
from time import sleep

# GPIO 2 est souvent la LED intégrée ou connectée à une LED externe
led = Pin(2, Pin.OUT)
print("Démarrage du programme...")

while True:
    led.value(1)  # Allumer la LED
    print("LED ON")
    sleep(1)
    led.value(0)  # Éteindre la LED
    print("LED OFF")
    sleep(1)
"""


@dataclass
class ProjectModel:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Nouveau Projet"
    description: str = ""
    board_id: str = "esp32_wroom_32"
    files: dict[str, str] = field(default_factory=lambda: {"main.py": DEFAULT_MAIN_PY})
    components: list[ComponentModel] = field(default_factory=list)
    connections: list[ConnectionModel] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    pedagogy_profile: dict | None = None

    def get_main_code(self) -> str:
        return self.files.get("main.py", "")

    def set_main_code(self, code: str) -> None:
        self.files["main.py"] = code
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        data = {
            "version": 1,
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "board_id": self.board_id,
            "files": self.files,
            "components": [c.to_dict() for c in self.components],
            "connections": [c.to_dict() for c in self.connections],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.pedagogy_profile is not None:
            data["pedagogy_profile"] = self.pedagogy_profile
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectModel":
        components = [ComponentModel.from_dict(c) for c in data.get("components", [])]
        connections = [ConnectionModel.from_dict(c) for c in data.get("connections", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Sans titre"),
            description=data.get("description", ""),
            board_id=data.get("board_id", "esp32_wroom_32"),
            files=data.get("files", {"main.py": DEFAULT_MAIN_PY}),
            components=components,
            connections=connections,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            pedagogy_profile=data.get("pedagogy_profile", None)
        )
