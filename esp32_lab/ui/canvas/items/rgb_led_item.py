"""
Rendu graphique ultra-réaliste d'une LED RGB 4 broches (Cathode commune)
Dôme diffusant 5mm, 4 pattes métalliques étamées alignées sur le pas standard de breadboard (8.5 px)
et synthèse additive dynamique des couleurs (Rouge, Vert, Bleu).
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PhysicalPinItem


class RGBLEDGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'une LED RGB 5mm à cathode commune."""

    def __init__(self, component_id: str, r: int = 255, g: int = 0, b: int = 0, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.val_r = max(0, min(255, int(r)))
        self.val_g = max(0, min(255, int(g)))
        self.val_b = max(0, min(255, int(b)))
        self.is_on = True

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches physiques réelles au pas 8.5 px (1 trou de breadboard MB-102)
        # R (Rouge), Cathode (GND - patte plus longue), G (Vert), B (Bleu)
        self.pin_r = PhysicalPinItem(component_id, "pin_r", "R (Rouge)", pin_length=22.0, pin_thickness=1.6, parent=self)
        self.pin_r.setPos(0, -12.75)

        self.pin_gnd = PhysicalPinItem(component_id, "pin_gnd", "Cathode (-) GND", pin_length=26.0, pin_thickness=1.6, parent=self)
        self.pin_gnd.setPos(0, -4.25)

        self.pin_g = PhysicalPinItem(component_id, "pin_g", "G (Vert)", pin_length=22.0, pin_thickness=1.6, parent=self)
        self.pin_g.setPos(0, 4.25)

        self.pin_b = PhysicalPinItem(component_id, "pin_b", "B (Bleu)", pin_length=22.0, pin_thickness=1.6, parent=self)
        self.pin_b.setPos(0, 12.75)

    def set_color_rgb(self, r: int, g: int, b: int):
        """Met à jour les composantes RVB (0 à 255) et rafraîchit l'affichage."""
        self.val_r = max(0, min(255, int(r)))
        self.val_g = max(0, min(255, int(g)))
        self.val_b = max(0, min(255, int(b)))
        self.is_on = (self.val_r > 5 or self.val_g > 5 or self.val_b > 5)
        self.update()

    def set_pwm(self, channel: str, freq_or_duty: int, duty: int = None):
        """Met à jour un canal PWM (duty 0 à 1023)."""
        if duty is None:
            duty = freq_or_duty  # Called with 2 args: (channel, duty)
        # else: Called with 3 args: (channel, freq, duty) — ignore freq
        val_255 = int(max(0, min(1023, duty)) * 255 / 1023)
        ch = channel.lower()
        if "r" in ch:
            self.val_r = val_255
        elif "g" in ch:
            self.val_g = val_255
        elif "b" in ch:
            self.val_b = val_255
        self.is_on = (self.val_r > 5 or self.val_g > 5 or self.val_b > 5)
        self.update()

    def boundingRect(self) -> QRectF:
        r = 38 if self.is_on else 24
        return QRectF(-r - 10, -28, 2 * r + 20, 56)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # Couleur composite résultante
        cur_color = QColor(self.val_r, self.val_g, self.val_b)
        has_light = self.is_on and (self.val_r > 10 or self.val_g > 10 or self.val_b > 10)

        # 1. Halo lumineux volumétrique si allumée
        if has_light:
            halo = QRadialGradient(-10, 0, 36)
            halo_col = QColor(cur_color)
            halo_col.setAlpha(120)
            halo.setColorAt(0.0, halo_col)
            halo_col2 = QColor(cur_color)
            halo_col2.setAlpha(30)
            halo.setColorAt(0.6, halo_col2)
            halo.setColorAt(1.0, QColor(cur_color.red(), cur_color.green(), cur_color.blue(), 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(halo))
            painter.drawEllipse(QRectF(-46, -36, 72, 72))

        # 2. 4 Pattes métalliques étamées
        lead_pen = QPen(QColor("#cbd5e1"), 2.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(lead_pen)
        # R, GND, G, B
        for y_pos in (-12.75, -4.25, 4.25, 12.75):
            painter.drawLine(QPointF(-2, y_pos), QPointF(2, y_pos))

        # 3. Dôme diffusant 5mm
        dome_rect = QRectF(-20, -12, 24, 24)
        dome_grad = QRadialGradient(-10, -2, 16)
        if has_light:
            dome_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
            dome_grad.setColorAt(0.3, cur_color)
            dome_grad.setColorAt(0.8, QColor(cur_color.darker(130)))
            dome_grad.setColorAt(1.0, QColor(cur_color.darker(170)))
        else:
            # Éteinte : résine blanche laiteuse/translucide
            dome_grad.setColorAt(0.0, QColor("#ffffff"))
            dome_grad.setColorAt(0.7, QColor("#e2e8f0"))
            dome_grad.setColorAt(1.0, QColor("#94a3b8"))

        painter.setPen(QPen(QColor(cur_color.darker(140) if has_light else "#64748b"), 1.2))
        painter.setBrush(QBrush(dome_grad))
        painter.drawEllipse(dome_rect)

        # 4. Collerette de base
        collar_rect = QRectF(-22, -13, 5, 26)
        painter.setPen(QPen(QColor("#94a3b8"), 0.8))
        painter.setBrush(QBrush(QColor("#cbd5e1" if not has_light else cur_color.lighter(120))))
        painter.drawRoundedRect(collar_rect, 2, 2)

        # 5. Électrodes internes visibles
        painter.setPen(QPen(QColor(255, 255, 255, 160), 0.9))
        painter.drawLine(QPointF(-14, -4), QPointF(-8, -4))
        painter.drawLine(QPointF(-14, 0), QPointF(-6, 0))
        painter.drawLine(QPointF(-14, 4), QPointF(-8, 4))

        # 6. Reflet spéculaire
        shine = QLinearGradient(-16, -10, -6, -2)
        shine.setColorAt(0.0, QColor(255, 255, 255, 200))
        shine.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shine))
        painter.drawEllipse(QRectF(-16, -8, 10, 6))

        # 7. Sélection
        if self.isSelected():
            painter.setPen(QPen(QColor("#38bdf8"), 1.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 4, 4)
