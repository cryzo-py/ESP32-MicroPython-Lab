"""
Module MicroPython simulé : neopixel
Gère les LED adressables WS2812B / NeoPixel avec protocole de commande couleur RGB.
"""

from typing import Callable

_neopixel_listeners: list[Callable[[int, list[tuple[int, int, int]]], None]] = []


def add_neopixel_listener(callback: Callable[[int, list[tuple[int, int, int]]], None]):
    if callback not in _neopixel_listeners:
        _neopixel_listeners.append(callback)


def remove_neopixel_listener(callback: Callable[[int, list[tuple[int, int, int]]], None]):
    if callback in _neopixel_listeners:
        _neopixel_listeners.remove(callback)


class NeoPixel:
    """Implémentation compatible du module officiel MicroPython neopixel."""

    def __init__(self, pin, n: int, bpp: int = 3, timing: int = 1):
        if hasattr(pin, "id"):
            self.pin_num = int(pin.id)
        elif hasattr(pin, "pin_num"):
            self.pin_num = int(pin.pin_num)
        else:
            try:
                self.pin_num = int(pin)
            except Exception:
                self.pin_num = 0
        self.n = max(1, int(n))
        self.bpp = bpp
        self.timing = timing
        # Buffer de pixels [(R, G, B), ...]
        self._pixels: list[tuple[int, int, int]] = [(0, 0, 0)] * self.n

    def __len__(self) -> int:
        return self.n

    def __setitem__(self, index: int, color: tuple[int, int, int]):
        if 0 <= index < self.n:
            r = max(0, min(255, int(color[0])))
            g = max(0, min(255, int(color[1])))
            b = max(0, min(255, int(color[2])))
            self._pixels[index] = (r, g, b)
        else:
            raise IndexError("Index NeoPixel hors limites")

    def __getitem__(self, index: int) -> tuple[int, int, int]:
        if 0 <= index < self.n:
            return self._pixels[index]
        raise IndexError("Index NeoPixel hors limites")

    def fill(self, color: tuple[int, int, int]):
        r = max(0, min(255, int(color[0])))
        g = max(0, min(255, int(color[1])))
        b = max(0, min(255, int(color[2])))
        self._pixels = [(r, g, b)] * self.n

    def write(self):
        """Transmet les données vers les composants graphiques du circuit."""
        for listener in _neopixel_listeners:
            try:
                listener(self.pin_num, list(self._pixels))
            except Exception:
                pass
