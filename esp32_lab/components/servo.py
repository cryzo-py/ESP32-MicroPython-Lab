"""
Runtime pour le composant Servomoteur (SG90)
"""

from .base import BaseComponentRuntime


class ServoRuntime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.angle: float = float(self.properties.get("angle", 90.0))

    def update_pwm(self, freq: int, duty: int):
        # 50 Hz typique : impulsion de 0.5ms (angle 0°) à 2.5ms (angle 180°)
        # Pour une période de 20ms (50Hz) :
        # duty 10-bit (0-1023) : 0.5ms = 26, 2.5ms = 128
        if freq > 0:
            duty_norm = max(26, min(128, duty))
            calculated_angle = (duty_norm - 26) / (128 - 26) * 180.0
            self.set_angle(calculated_angle)

    def set_angle(self, angle: float):
        self.angle = max(0.0, min(180.0, float(angle)))
        self.properties["angle"] = self.angle
        self.state_changed.emit({
            "component_id": self.component_id,
            "angle": self.angle
        })
