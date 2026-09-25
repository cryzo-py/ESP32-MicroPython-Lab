"""
Runtime pour le composant Buzzer
"""

from .base import BaseComponentRuntime


class BuzzerRuntime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.is_active = False
        self.frequency = 0

    def update_pin(self, pin_id: str, value: int | float):
        if pin_id in ("pos", "sig"):
            active = bool(value)
            if active != self.is_active:
                self.is_active = active
                self.state_changed.emit({
                    "component_id": self.component_id,
                    "is_active": self.is_active,
                    "frequency": self.frequency
                })

    def update_pwm(self, freq: int, duty: int):
        active = (duty > 0 and freq > 20)
        if active != self.is_active or freq != self.frequency:
            self.is_active = active
            self.frequency = freq
            self.state_changed.emit({
                "component_id": self.component_id,
                "is_active": self.is_active,
                "frequency": self.frequency
            })
