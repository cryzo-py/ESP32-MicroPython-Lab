"""
Module 'hcsr04' simulé pour capteur de distance à ultrasons HC-SR04
"""

_hcsr04_distances: dict[tuple[int, int], float] = {}


def set_distance(trigger_pin: int, echo_pin: int, distance_cm: float):
    _hcsr04_distances[(trigger_pin, echo_pin)] = float(distance_cm)


def get_distance(trigger_pin: int, echo_pin: int) -> float:
    return _hcsr04_distances.get((trigger_pin, echo_pin), 25.0)


class HCSR04:
    def __init__(self, trigger_pin, echo_pin, echo_timeout_us: int = 30000):
        self.trig = trigger_pin.id if hasattr(trigger_pin, "id") else int(trigger_pin)
        self.echo = echo_pin.id if hasattr(echo_pin, "id") else int(echo_pin)
        self.echo_timeout_us = echo_timeout_us

    def distance_cm(self) -> float:
        return get_distance(self.trig, self.echo)

    def distance_mm(self) -> float:
        return self.distance_cm() * 10.0
