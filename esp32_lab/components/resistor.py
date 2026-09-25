"""
Runtime pour le composant Résistance
"""

from .base import BaseComponentRuntime


class ResistorRuntime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.resistance = self.properties.get("value", 220)
        self.pin1_val = 0
        self.pin2_val = 0

    def update_pin(self, pin_id: str, value: int | float):
        if pin_id == "pin1":
            self.pin1_val = value
        elif pin_id == "pin2":
            self.pin2_val = value

    def get_pin_value(self, pin_id: str) -> int | float:
        # Transmet le signal vers l'autre patte
        if pin_id == "pin1":
            return self.pin2_val
        return self.pin1_val
