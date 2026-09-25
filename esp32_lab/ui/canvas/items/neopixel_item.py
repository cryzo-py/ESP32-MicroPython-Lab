"""
Rendu graphique ultra-réaliste d'un module / anneau LED RGB Adressable NeoPixel (WS2812B)
Boîtiers CMS 5050 avec puce intégrée, mélange de couleurs 24 bits et broches (5V, DIN, DOUT, GND).
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PinAnchorItem


class NeoPixelGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un anneau / module 8 LED RGB adressables WS2812B."""

    def __init__(self, component_id: str, num_leds: int = 8, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.num_leds = max(1, min(16, int(num_leds)))
        self.colors: list[tuple[int, int, int]] = [(0, 0, 0)] * self.num_leds

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches d'interface en bas : 5V, DIN, DOUT, GND
        self.pin_5v = PinAnchorItem(component_id, "5v", "5V / VCC", parent=self)
        self.pin_5v.setPos(-24, 38)

        self.pin_din = PinAnchorItem(component_id, "din", "DIN (Signal IN)", parent=self)
        self.pin_din.setPos(-8, 38)

        self.pin_dout = PinAnchorItem(component_id, "dout", "DOUT (Signal OUT)", parent=self)
        self.pin_dout.setPos(8, 38)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(24, 38)

    @property
    def led_colors(self) -> list[tuple[int, int, int]]:
        return self.colors

    def get_anchor_pins(self) -> list[PinAnchorItem]:
        return [c for c in self.childItems() if isinstance(c, PinAnchorItem)]

    def boundingRect(self) -> QRectF:
        return QRectF(-48, -48, 96, 96)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée circulaire sous le module
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawEllipse(QPointF(2, 3), 36, 36)

        # 2. PCB circulaire noir mat satiné
        pcb_grad = QRadialGradient(0, 0, 36)
        pcb_grad.setColorAt(0.0, QColor("#1e1e24"))
        pcb_grad.setColorAt(0.8, QColor("#141417"))
        pcb_grad.setColorAt(1.0, QColor("#09090b"))

        painter.setPen(QPen(QColor("#27272a"), 1.2))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawEllipse(QPointF(0, 0), 36, 36)

        # Trou central du beignet d'anneau
        painter.setBrush(QBrush(QColor("#111827"))) # Fond de l'espace de travail
        painter.drawEllipse(QPointF(0, 0), 14, 14)

        # 3. Connecteur 4 broches en bas (5V, DIN, DOUT, GND)
        self._paint_connector(painter)

        # 4. Les boîtiers CMS 5050 répartis en cercle avec émission de couleur
        self._paint_leds(painter)

    def _paint_connector(self, painter: QPainter):
        """Barrette 4 broches dorées au bas de l'anneau."""
        c_rect = QRectF(-30, 32, 60, 9)
        painter.setPen(QPen(QColor("#27272a"), 1))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(c_rect, 1.5, 1.5)

        pins_meta = [(-24, "5V"), (-8, "DI"), (8, "DO"), (24, "GND")]
        font_p = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font_p)

        for px, label in pins_meta:
            # Alvéole carrée avec contact doré
            painter.setPen(QPen(QColor("#3f3f46"), 0.6))
            painter.setBrush(QBrush(QColor("#09090b")))
            painter.drawRect(QRectF(px - 2.5, 33.5, 5, 5))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawRect(QRectF(px - 1.2, 34.8, 2.4, 2.4))

            # Sérigraphie
            painter.setPen(QColor("#f8fafc"))
            painter.drawText(QRectF(px - 8, 26, 16, 6), Qt.AlignCenter, label)

    def _paint_leds(self, painter: QPainter):
        """Dessine chaque puce CMS 5050 avec sa couleur active et son halo lumineux."""
        ring_radius = 25.0
        angle_step = 360.0 / self.num_leds

        for i in range(self.num_leds):
            angle_deg = -90.0 + i * angle_step
            angle_rad = math.radians(angle_deg)
            cx = ring_radius * math.cos(angle_rad)
            cy = ring_radius * math.sin(angle_rad)

            color = self.colors[i] if i < len(self.colors) else (0, 0, 0)
            r, g, b = color
            is_lit = (r + g + b) > 5

            # 1. Halo lumineux si allumé
            if is_lit:
                glow = QRadialGradient(cx, cy, 14)
                glow.setColorAt(0.0, QColor(r, g, b, 220))
                glow.setColorAt(0.5, QColor(r, g, b, 90))
                glow.setColorAt(1.0, QColor(r, g, b, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(glow))
                painter.drawEllipse(QPointF(cx, cy), 14, 14)

            # 2. Boîtier blanc CMS 5050 carré
            led_rect = QRectF(cx - 3.5, cy - 3.5, 7, 7)
            painter.setPen(QPen(QColor("#cbd5e1"), 0.6))
            painter.setBrush(QBrush(QColor("#f8fafc")))
            painter.drawRoundedRect(led_rect, 0.8, 0.8)

            # 4 pastilles dorées de soudure aux coins
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawRect(QRectF(cx - 4.2, cy - 3.2, 1.2, 1.5))
            painter.drawRect(QRectF(cx + 3.0, cy - 3.2, 1.2, 1.5))
            painter.drawRect(QRectF(cx - 4.2, cy + 1.7, 1.2, 1.5))
            painter.drawRect(QRectF(cx + 3.0, cy + 1.7, 1.2, 1.5))

            # 3. Cavité optique centrale en silicone translucide
            lens_color = QColor(r, g, b) if is_lit else QColor("#e2e8f0")
            lens_grad = QRadialGradient(cx, cy, 2.5)
            lens_grad.setColorAt(0.0, QColor("#ffffff") if is_lit else QColor("#ffffff"))
            lens_grad.setColorAt(0.6, lens_color)
            lens_grad.setColorAt(1.0, lens_color.darker(150))

            painter.setBrush(QBrush(lens_grad))
            painter.drawEllipse(QPointF(cx, cy), 2.4, 2.4)

    def set_colors(self, colors: list[tuple[int, int, int]]):
        self.colors = list(colors)
        self.update()

    def clear(self):
        """Éteint toutes les LEDs de l'anneau."""
        self.colors = [(0, 0, 0)] * self.num_leds
        self.update()
