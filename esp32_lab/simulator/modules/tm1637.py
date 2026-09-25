"""
Module MicroPython de simulation pour afficheur digital 4 digits TM1637.
Fournit une API standardisée compatible avec les bibliothèques courantes MicroPython TM1637.
"""

from typing import Callable

_tm1637_listeners: list[Callable[[str, bool], None]] = []


def add_tm1637_listener(callback: Callable[[str, bool], None]):
    if callback not in _tm1637_listeners:
        _tm1637_listeners.append(callback)


def remove_tm1637_listener(callback: Callable[[str, bool], None]):
    if callback in _tm1637_listeners:
        _tm1637_listeners.remove(callback)


def _notify_display(text: str, colon: bool = False):
    for cb in _tm1637_listeners:
        try:
            cb(text, colon)
        except Exception:
            pass


class TM1637:
    """Pilote MicroPython émulé pour afficheur 4 digits 7 segments TM1637."""

    def __init__(self, clk=None, dio=None, brightness=7):
        self.clk = clk
        self.dio = dio
        self._brightness = brightness
        self._text = "    "
        self._colon = False

    def brightness(self, val: int):
        self._brightness = max(0, min(7, int(val)))

    def show(self, text: str, colon: bool = False):
        """Affiche un texte ou des chiffres sur les 4 digits."""
        self._text = str(text)
        self._colon = colon or (":" in self._text)
        _notify_display(self._text, self._colon)

    def number(self, num: int):
        """Affiche un nombre entier (0-9999 ou négatif)."""
        formatted = f"{num:4d}"
        self.show(formatted, colon=False)

    def numbers(self, num1: int, num2: int, colon: bool = True):
        """Affiche deux nombres format horloge MM:SS ou HH:MM."""
        formatted = f"{num1:02d}{num2:02d}"
        self.show(formatted, colon=colon)

    def temperature(self, num: int):
        """Affiche une température (ex: 24°C)."""
        formatted = f"{num:2d}C "
        self.show(formatted, colon=False)

    def clear(self):
        self.show("    ", colon=False)
