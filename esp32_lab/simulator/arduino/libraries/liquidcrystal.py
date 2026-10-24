"""
Bibliothèque virtuelle 'LiquidCrystal' pour Arduino C.
Permet de piloter un afficheur LCD standard (16x2 ou 20x4) en mode 4 bits ou 8 bits.
"""

from __future__ import annotations
from typing import Any
from ...modules.liquidcrystal_i2c import _lcd_listeners


class VirtualLiquidCrystal:
    """Implémentation virtuelle de la bibliothèque LiquidCrystal Arduino."""

    def __init__(self, rs=None, rw_or_en=None, d4_or_en=None, d4=None, d5=None, d6=None, d7=None):
        self.num_cols = 16
        self.num_rows = 2
        self.cursor_col = 0
        self.cursor_row = 0
        self.lines: list[str] = [" " * self.num_cols for _ in range(self.num_rows)]

    def begin(self, cols: int = 16, rows: int = 2):
        """Initialise la géométrie de l'écran (colonnes, lignes)."""
        self.num_cols = max(1, int(cols))
        self.num_rows = max(1, int(rows))
        self.clear()

    def clear(self):
        """Efface l'écran et replace le curseur en haut à gauche (0, 0)."""
        self.cursor_col = 0
        self.cursor_row = 0
        self.lines = [" " * self.num_cols for _ in range(self.num_rows)]
        self._notify()

    def home(self):
        """Replace le curseur en position initiale sans effacer le texte."""
        self.cursor_col = 0
        self.cursor_row = 0

    def setCursor(self, col: int, row: int):
        """Positionne le curseur aux coordonnées (col, row)."""
        self.cursor_col = max(0, min(self.num_cols - 1, int(col)))
        self.cursor_row = max(0, min(self.num_rows - 1, int(row)))

    def print(self, val: Any) -> int:
        """Affiche une valeur ou chaîne à la position actuelle du curseur."""
        text = str(val)
        chars_written = 0
        for ch in text:
            if ch == '\n':
                self.cursor_row = (self.cursor_row + 1) % self.num_rows
                self.cursor_col = 0
            elif ch == '\r':
                self.cursor_col = 0
            else:
                line_chars = list(self.lines[self.cursor_row])
                if self.cursor_col < self.num_cols:
                    line_chars[self.cursor_col] = ch
                    self.lines[self.cursor_row] = "".join(line_chars)
                    self.cursor_col += 1
                    chars_written += 1
                if self.cursor_col >= self.num_cols:
                    self.cursor_col = 0
                    self.cursor_row = (self.cursor_row + 1) % self.num_rows

        self._notify()
        return chars_written

    def println(self, val: Any = "") -> int:
        """Affiche une valeur suivie d'un retour à la ligne."""
        n = self.print(str(val) + "\n")
        return n

    def write(self, val: Any) -> int:
        """Écrit un caractère individuel."""
        if isinstance(val, int):
            ch = chr(val)
        else:
            ch = str(val)[0] if val else ""
        return self.print(ch)

    def _notify(self):
        """Notifie l'interface graphique de la mise à jour de l'affichage."""
        for listener in _lcd_listeners:
            try:
                listener(self.lines)
            except Exception:
                pass
