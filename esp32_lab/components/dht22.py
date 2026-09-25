"""
Runtime pour le capteur de température et d'humidité DHT22
"""

from ..simulator.modules.dht import set_sensor_data
from .base import BaseComponentRuntime


class DHT22Runtime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.temperature = float(self.properties.get("temperature", 24.5))
        self.humidity = float(self.properties.get("humidity", 55.0))
        self.connected_pin: int | None = self.properties.get("connected_pin", 4)
        self._sync()

    def set_values(self, temp: float, hum: float):
        self.temperature = float(temp)
        self.humidity = float(hum)
        self.properties["temperature"] = self.temperature
        self.properties["humidity"] = self.humidity
        self._sync()
        self.state_changed.emit({
            "component_id": self.component_id,
            "temperature": self.temperature,
            "humidity": self.humidity
        })

    def set_pin(self, pin: int):
        self.connected_pin = pin
        self.properties["connected_pin"] = pin
        self._sync()

    def _sync(self):
        if self.connected_pin is not None:
            set_sensor_data(self.connected_pin, self.temperature, self.humidity)
