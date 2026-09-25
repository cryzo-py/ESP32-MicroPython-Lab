"""
Runtime pour l'écran OLED SSD1306 I2C (128x64)
"""

from ..simulator.modules.machine import I2C
from ..simulator.modules.ssd1306 import add_display_listener, remove_display_listener
from .base import BaseComponentRuntime


class OLEDRuntime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.width = int(self.properties.get("width", 128))
        self.height = int(self.properties.get("height", 64))
        self.address = int(self.properties.get("address", 0x3C))
        
        # Buffer d'affichage 2D
        self.buffer = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # Enregistrement I2C et listener SSD1306
        I2C.register_device(self.address, self)
        add_display_listener(self._on_display_updated)

    def _on_display_updated(self, width: int, height: int, buffer: list[list[int]]):
        self.width = width
        self.height = height
        self.buffer = [row[:] for row in buffer]
        self.state_changed.emit({
            "component_id": self.component_id,
            "width": self.width,
            "height": self.height,
            "buffer": self.buffer
        })

    def write_i2c(self, data: bytes | bytearray):
        # Commande / données brutes I2C
        pass

    def cleanup(self):
        I2C.unregister_device(self.address)
        remove_display_listener(self._on_display_updated)
