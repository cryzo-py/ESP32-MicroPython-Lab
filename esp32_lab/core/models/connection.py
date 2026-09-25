"""
Modèle de connexion électrique (fil / wire) entre broches
"""

from dataclasses import dataclass, field
import uuid


@dataclass
class ConnectionModel:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_component: str = ""    # id du composant ou "esp32"
    from_pin: str = ""          # id ou nom de la broche
    to_component: str = ""      # id du composant ou "esp32"
    to_pin: str = ""            # id ou nom de la broche
    color: str = "#ef4444"      # Couleur hexadécimale du fil (rouge, vert, bleu, noir, etc.)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_component": self.from_component,
            "from_pin": self.from_pin,
            "to_component": self.to_component,
            "to_pin": self.to_pin,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectionModel":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            from_component=data.get("from_component", ""),
            from_pin=data.get("from_pin", ""),
            to_component=data.get("to_component", ""),
            to_pin=data.get("to_pin", ""),
            color=data.get("color", "#ef4444"),
        )
