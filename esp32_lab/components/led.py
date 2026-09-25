"""
Runtime pour le composant LED
"""

from .base import BaseComponentRuntime


class LEDRuntime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.color = self.properties.get("color", "red")
        self.is_on = False
        self._anode_val = 0
        self._cathode_val = 0

    def update_pin(self, pin_id: str, value: int | float):
        if pin_id == "anode":
            self._anode_val = 1 if value else 0
        elif pin_id == "cathode":
            self._cathode_val = 1 if value else 0
            
        # La LED s'allume si Anode > Cathode
        new_state = (self._anode_val == 1 and self._cathode_val == 0)
        if new_state != self.is_on:
            self.is_on = new_state
            self.state_changed.emit({
                "component_id": self.component_id,
                "is_on": self.is_on,
                "color": self.color
            })
