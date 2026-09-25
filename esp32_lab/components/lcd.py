"""
Runtime pour l'afficheur LCD 16x2 (I2C)
"""

from ..simulator.modules.liquidcrystal_i2c import add_lcd_listener, remove_lcd_listener
from .base import BaseComponentRuntime


class LCD16x2Runtime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.num_lines = int(self.properties.get("lines", 2))
        self.num_cols = int(self.properties.get("cols", 16))
        self.lines = [" " * self.num_cols for _ in range(self.num_lines)]
        
        add_lcd_listener(self._on_lcd_updated)

    def _on_lcd_updated(self, lines: list[str]):
        self.lines = lines
        self.state_changed.emit({
            "component_id": self.component_id,
            "lines": self.lines
        })

    def cleanup(self):
        remove_lcd_listener(self._on_lcd_updated)
