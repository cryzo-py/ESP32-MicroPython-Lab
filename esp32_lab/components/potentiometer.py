"""
Runtime pour le composant Potentiomètre
"""

from .base import BaseComponentRuntime


class PotentiometerRuntime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        # Valeur ADC brute de 0 à 4095
        self.raw_value = int(self.properties.get("raw_value", 2048))

    def set_value(self, val: int):
        self.raw_value = max(0, min(4095, int(val)))
        self.properties["raw_value"] = self.raw_value
        self.state_changed.emit({
            "component_id": self.component_id,
            "raw_value": self.raw_value,
            "voltage": round(self.raw_value * 3.3 / 4095, 2)
        })

    def get_pin_value(self, pin_id: str) -> int:
        if pin_id == "sig":
            return self.raw_value
        return 0
