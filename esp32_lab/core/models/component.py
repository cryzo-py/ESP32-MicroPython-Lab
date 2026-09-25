"""
Modèles pour les composants virtuels du circuit
"""

from dataclasses import dataclass, field
import uuid


@dataclass
class ComponentPin:
    id: str               # ex: "anode", "cathode", "pin1", "pin2"
    name: str             # ex: "+", "-", "VCC", "GND", "SIG"
    x_offset: float = 0.0 # Position relative par rapport au composant
    y_offset: float = 0.0


@dataclass
class ComponentModel:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str = "generic" # "led", "resistor", "button", "potentiometer", etc.
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    properties: dict = field(default_factory=dict)
    pins: list[ComponentPin] = field(default_factory=list)
    pin_insertions: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "properties": self.properties,
            "pins": [{"id": p.id, "name": p.name, "x_offset": p.x_offset, "y_offset": p.y_offset} for p in self.pins],
            "pin_insertions": self.pin_insertions
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentModel":
        pins = [
            ComponentPin(
                id=p["id"],
                name=p["name"],
                x_offset=p.get("x_offset", 0.0),
                y_offset=p.get("y_offset", 0.0)
            ) for p in data.get("pins", [])
        ]
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            type=data.get("type", "generic"),
            name=data.get("name", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            rotation=data.get("rotation", 0.0),
            properties=data.get("properties", {}),
            pins=pins,
            pin_insertions=data.get("pin_insertions", {})
        )
