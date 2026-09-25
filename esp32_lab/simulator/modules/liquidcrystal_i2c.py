"""
Module 'liquidcrystal_i2c' simulé pour afficheur LCD 16x2 (I2C)
"""

from typing import Callable

_lcd_listeners: list[Callable[[list[str]], None]] = []


def add_lcd_listener(callback: Callable[[list[str]], None]):
    if callback not in _lcd_listeners:
        _lcd_listeners.append(callback)


def remove_lcd_listener(callback: Callable[[list[str]], None]):
    if callback in _lcd_listeners:
        _lcd_listeners.remove(callback)


class I2cLcd:
    def __init__(self, i2c, i2c_addr: int = 0x27, num_lines: int = 2, num_columns: int = 16):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.cursor_x = 0
        self.cursor_y = 0
        # Grille 2 lignes x 16 colonnes
        self.lines = [" " * num_columns for _ in range(num_lines)]
        self._notify()

    def clear(self):
        self.cursor_x = 0
        self.cursor_y = 0
        self.lines = [" " * self.num_columns for _ in range(self.num_lines)]
        self._notify()

    def move_to(self, cursor_x: int, cursor_y: int):
        self.cursor_x = max(0, min(self.num_columns - 1, cursor_x))
        self.cursor_y = max(0, min(self.num_lines - 1, cursor_y))

    def putstr(self, string: str):
        for char in str(string):
            if char == '\n':
                self.cursor_y = (self.cursor_y + 1) % self.num_lines
                self.cursor_x = 0
            elif char == '\r':
                self.cursor_x = 0
            else:
                line_chars = list(self.lines[self.cursor_y])
                if self.cursor_x < self.num_columns:
                    line_chars[self.cursor_x] = char
                    self.lines[self.cursor_y] = "".join(line_chars)
                    self.cursor_x += 1
                if self.cursor_x >= self.num_columns:
                    self.cursor_x = 0
                    self.cursor_y = (self.cursor_y + 1) % self.num_lines
        self._notify()

    def putchar(self, char: str):
        self.putstr(char)

    def _notify(self):
        for cb in _lcd_listeners:
            try:
                cb(self.lines[:])
            except Exception:
                pass
