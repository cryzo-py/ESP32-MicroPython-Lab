"""
Runtime pour le capteur de distance à ultrasons HC-SR04
"""

from ..simulator.modules.hcsr04 import set_distance
from .base import BaseComponentRuntime


class HCSR04Runtime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.distance_cm = float(self.properties.get("distance_cm", 25.0))
        self.trig_pin: int = int(self.properties.get("trig_pin", 5))
        self.echo_pin: int = int(self.properties.get("echo_pin", 18))
        self._sync()

    def set_distance(self, distance_cm: float):
        self.distance_cm = max(2.0, min(400.0, float(distance_cm)))
        self.properties["distance_cm"] = self.distance_cm
        self._sync()
        self.state_changed.emit({
            "component_id": self.component_id,
            "distance_cm": self.distance_cm
        })

    def configure_pins(self, trig_pin: int, echo_pin: int):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.properties["trig_pin"] = trig_pin
        self.properties["echo_pin"] = echo_pin
        self._sync()

    def _sync(self):
        set_distance(self.trig_pin, self.echo_pin, self.distance_cm)
