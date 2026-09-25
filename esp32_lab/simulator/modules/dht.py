"""
Module 'dht' simulé pour capteurs de température et humidité DHT11 et DHT22
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .machine import Pin

_dht_sensors: dict[int, dict] = {}


def set_sensor_data(pin_id: int, temperature: float, humidity: float):
    _dht_sensors[pin_id] = {
        "temperature": temperature,
        "humidity": humidity
    }


def get_sensor_data(pin_id: int) -> dict:
    return _dht_sensors.setdefault(pin_id, {"temperature": 24.0, "humidity": 50.0})


class DHTBase:
    def __init__(self, pin):
        self.pin = pin
        self._pin_id = pin.id if hasattr(pin, "id") else int(pin)
        self._temp = 24.0
        self._hum = 50.0

    def measure(self):
        data = get_sensor_data(self._pin_id)
        self._temp = data.get("temperature", 24.0)
        self._hum = data.get("humidity", 50.0)

    def temperature(self) -> float:
        return self._temp

    def humidity(self) -> float:
        return self._hum


class DHT11(DHTBase):
    def temperature(self) -> int:
        return int(self._temp)

    def humidity(self) -> int:
        return int(self._hum)


class DHT22(DHTBase):
    pass
