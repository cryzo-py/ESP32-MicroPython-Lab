"""
Rendu graphique ultra-réaliste d'un joystick analogique 2 axes KY-023
Module PCB bleu avec chapeau ergonomique de pouce noir, deux potentiomètres
orthogonaux et 5 broches de raccordement (GND, +5V, VRx, VRy, SW).
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


class JoystickGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un joystick analogique 2 axes KY-023."""

    def __init__(self, component_id: str, x_val: int = 2048, y_val: int = 2048, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.x_val = max(0, min(4095, int(x_val)))
        self.y_val = max(0, min(4095, int(y_val)))
        self.sw_pressed = False

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 5 broches physiques réelles au pas standard 8.5 px
        # GND, +5V, VRx (Axe X), VRy (Axe Y), SW (Bouton poussoir)
        self.pin_gnd = PhysicalPinItem(component_id, "gnd", "GND (Masse)", pin_length=18.0, pin_thickness=1.8, parent=self)
        self.pin_gnd.setPos(-17.0, 22.0)

        self.pin_vcc = PhysicalPinItem(component_id, "vcc", "+5V (Alimentation)", pin_length=18.0, pin_thickness=1.8, parent=self)
        self.pin_vcc.setPos(-8.5, 22.0)

        self.pin_vrx = PhysicalPinItem(component_id, "vrx", "VRx (Axe X - ADC)", pin_length=18.0, pin_thickness=1.8, parent=self)
        self.pin_vrx.setPos(0, 22.0)

        self.pin_vry = PhysicalPinItem(component_id, "vry", "VRy (Axe Y - ADC)", pin_length=18.0, pin_thickness=1.8, parent=self)
        self.pin_vry.setPos(8.5, 22.0)

        self.pin_sw = PhysicalPinItem(component_id, "sw", "SW (Bouton Poussoir)", pin_length=18.0, pin_thickness=1.8, parent=self)
        self.pin_sw.setPos(17.0, 22.0)

    def set_position(self, x_val: int, y_val: int, sw_pressed: bool = False):
        """Met à jour la position des axes et l'état du switch."""
        self.x_val = max(0, min(4095, int(x_val)))
        self.y_val = max(0, min(4095, int(y_val)))
        self.sw_pressed = bool(sw_pressed)
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-26, -26, 52, 54)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. PCB bleu de support
        pcb_rect = QRectF(-24, -22, 48, 40)
        pcb_grad = QLinearGradient(-24, -22, 24, 18)
        pcb_grad.setColorAt(0.0, QColor("#1e3a8a"))
        pcb_grad.setColorAt(1.0, QColor("#172554"))
        painter.setPen(QPen(QColor("#0f172a"), 1.0))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(pcb_rect, 4, 4)

        # 2. Potentiomètres latéraux métalliques (boîtiers métalliques argentés)
        pot_pen = QPen(QColor("#64748b"), 0.8)
        painter.setPen(pot_pen)
        painter.setBrush(QBrush(QColor("#94a3b8")))
        painter.drawRect(QRectF(-22, -10, 4, 16)) # Potentiomètre X
        painter.drawRect(QRectF(-8, -20, 16, 4)) # Potentiomètre Y

        # Sérigraphie des broches
        painter.setFont(painter.font())
        painter.setPen(QColor("#93c5fd"))

        # 3. Base du cardan central (anneau métallique chromé)
        painter.setPen(QPen(QColor("#cbd5e1"), 1.0))
        painter.setBrush(QBrush(QColor("#334155")))
        painter.drawEllipse(QRectF(-16, -16, 32, 32))

        # 4. Chapeau ergonomique noir orientable
        # Décalage dynamique selon la position des axes (-4px à +4px)
        dx = (self.x_val - 2048) / 2048.0 * 5.0
        dy = (self.y_val - 2048) / 2048.0 * 5.0

        thumb_center = QPointF(dx, dy)
        thumb_grad = QRadialGradient(thumb_center.x() - 3, thumb_center.y() - 3, 14)
        thumb_grad.setColorAt(0.0, QColor("#475569"))
        thumb_grad.setColorAt(0.5, QColor("#1e293b"))
        thumb_grad.setColorAt(1.0, QColor("#090d16"))

        painter.setPen(QPen(QColor("#020617"), 1.2))
        painter.setBrush(QBrush(thumb_grad))
        painter.drawEllipse(thumb_center, 12, 12)

        # Cupule centrale du pouce (concavité)
        cup_grad = QRadialGradient(thumb_center.x(), thumb_center.y(), 7)
        if self.sw_pressed:
            cup_grad.setColorAt(0.0, QColor("#2563eb"))
            cup_grad.setColorAt(1.0, QColor("#1d4ed8"))
        else:
            cup_grad.setColorAt(0.0, QColor("#020617"))
            cup_grad.setColorAt(0.7, QColor("#0f172a"))
            cup_grad.setColorAt(1.0, QColor("#334155"))

        painter.setPen(QPen(QColor("#475569"), 0.8))
        painter.setBrush(QBrush(cup_grad))
        painter.drawEllipse(thumb_center, 6.5, 6.5)

        # 5. Broches descendantes
        lead_pen = QPen(QColor("#cbd5e1"), 2.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(lead_pen)
        for x_pin in (-17.0, -8.5, 0, 8.5, 17.0):
            painter.drawLine(QPointF(x_pin, 18), QPointF(x_pin, 22))

        # 6. Sélection
        if self.isSelected():
            painter.setPen(QPen(QColor("#38bdf8"), 1.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 4, 4)
