"""
Rendu graphique ultra-réaliste d'un bouton poussoir tactile 6x6 mm
Boîtier plastique noir thermorésistant, armature métallique supérieure sertie par 4 rivets,
actionneur cylindrique coloré avec déformation à l'enfoncement, et 4 pattes coudées métalliques.
"""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
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

from .pin_item import PinAnchorItem, PhysicalPinItem


class ButtonGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un bouton poussoir tactile standard 6x6 mm."""

    button_pressed = Signal(str)
    button_released = Signal(str)

    def __init__(self, component_id: str, color_name: str = "blue", parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.color_name = color_name
        self.is_pressed = False

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches métalliques traversantes physiques (2 à gauche, 2 à droite)
        # Pins 1a et 1b reliées en interne, 2a et 2b reliées en interne
        self.pin1 = PhysicalPinItem(component_id, "pin1", "1a", pin_length=16.0, pin_thickness=1.5, parent=self)
        self.pin1.setPos(-19, -8.5)

        self.pin2 = PhysicalPinItem(component_id, "pin2", "1b", pin_length=16.0, pin_thickness=1.5, parent=self)
        self.pin2.setPos(19, -8.5)

        self.pin3 = PhysicalPinItem(component_id, "pin3", "2a", pin_length=16.0, pin_thickness=1.5, parent=self)
        self.pin3.setPos(-19, 8.5)

        self.pin4 = PhysicalPinItem(component_id, "pin4", "2b", pin_length=16.0, pin_thickness=1.5, parent=self)
        self.pin4.setPos(19, 8.5)

    def boundingRect(self) -> QRectF:
        return QRectF(-25, -20, 50, 40)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le bouton
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawRoundedRect(QRectF(-14, -13, 30, 30), 3, 3)

        # 2. Les 4 pattes métalliques coudées étamées
        self._paint_pins(painter)

        # 3. Boîtier plastique noir de base
        self._paint_plastic_body(painter)

        # 4. Plaque supérieure métallique avec rivets d'angle
        self._paint_metal_cover(painter)

        # 5. Poussoir tactile central (effet d'enfoncement physique)
        self._paint_actuator(painter)

    def _paint_pins(self, painter: QPainter):
        """Pattes métalliques recourbées pour insertion dans la plaque breadboard."""
        pin_grad = QLinearGradient(-2, 0, 2, 0)
        pin_grad.setColorAt(0.0, QColor("#475569"))
        pin_grad.setColorAt(0.4, QColor("#f1f5f9"))
        pin_grad.setColorAt(1.0, QColor("#334155"))

        painter.setPen(QPen(QColor("#334155"), 0.6))
        painter.setBrush(QBrush(pin_grad))

        # 1. Patte 1a (gauche haut, ancre à x=-19, y=-8.5)
        painter.drawRoundedRect(QRectF(-20.5, -10.0, 7.8, 3.0), 0.5, 0.5)
        # Ombre d'insertion dans le trou
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(15, 23, 42, 190)))
        painter.drawRect(QRectF(-20.2, -9.5, 2.4, 2.0))

        # 2. Patte 2a (gauche bas, ancre à x=-19, y=8.5)
        painter.setPen(QPen(QColor("#334155"), 0.6))
        painter.setBrush(QBrush(pin_grad))
        painter.drawRoundedRect(QRectF(-20.5, 7.0, 7.8, 3.0), 0.5, 0.5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(15, 23, 42, 190)))
        painter.drawRect(QRectF(-20.2, 7.5, 2.4, 2.0))

        # 3. Patte 1b (droite haut, ancre à x=19, y=-8.5)
        painter.setPen(QPen(QColor("#334155"), 0.6))
        painter.setBrush(QBrush(pin_grad))
        painter.drawRoundedRect(QRectF(12.7, -10.0, 7.8, 3.0), 0.5, 0.5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(15, 23, 42, 190)))
        painter.drawRect(QRectF(17.8, -9.5, 2.4, 2.0))

        # 4. Patte 2b (droite bas, ancre à x=19, y=8.5)
        painter.setPen(QPen(QColor("#334155"), 0.6))
        painter.setBrush(QBrush(pin_grad))
        painter.drawRoundedRect(QRectF(12.7, 7.0, 7.8, 3.0), 0.5, 0.5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(15, 23, 42, 190)))
        painter.drawRect(QRectF(17.8, 7.5, 2.4, 2.0))

    def _paint_plastic_body(self, painter: QPainter):
        """Corps carré en plastique moulé noir/anthracite."""
        body_grad = QLinearGradient(-13, -13, 13, 13)
        body_grad.setColorAt(0.0, QColor("#27272a"))
        body_grad.setColorAt(1.0, QColor("#09090b"))

        painter.setPen(QPen(QColor("#3f3f46"), 1))
        painter.setBrush(QBrush(body_grad))
        painter.drawRoundedRect(QRectF(-13, -13, 26, 26), 2, 2)

    def _paint_metal_cover(self, painter: QPainter):
        """Plaque de maintien métallique supérieure avec rivets aux 4 coins."""
        cover_grad = QLinearGradient(-11, -11, 11, 11)
        cover_grad.setColorAt(0.0, QColor("#f1f5f9"))
        cover_grad.setColorAt(0.3, QColor("#cbd5e1"))
        cover_grad.setColorAt(0.7, QColor("#94a3b8"))
        cover_grad.setColorAt(1.0, QColor("#e2e8f0"))

        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.setBrush(QBrush(cover_grad))
        painter.drawRoundedRect(QRectF(-11, -11, 22, 22), 2, 2)

        # 4 Rivets circulaires de sertissage aux coins
        rivet_coords = [(-8, -8), (8, -8), (-8, 8), (8, 8)]
        painter.setPen(QPen(QColor("#475569"), 0.6))
        painter.setBrush(QBrush(QColor("#e2e8f0")))
        for rx, ry in rivet_coords:
            painter.drawEllipse(QPointF(rx, ry), 1.6, 1.6)
            painter.setBrush(QBrush(QColor("#64748b")))
            painter.drawEllipse(QPointF(rx, ry), 0.8, 0.8)

    def _paint_actuator(self, painter: QPainter):
        """Poussoir cylindrique avec relief 3D et état pressé."""
        radius = 6.2 if not self.is_pressed else 5.4
        offset_y = 0.0 if not self.is_pressed else 0.8

        # Couleurs selon color_name
        base_c = QColor("#0284c7") if self.color_name == "blue" else QColor("#dc2626")
        dark_c = base_c.darker(180)
        light_c = base_c.lighter(140)

        # Dégradé radial pour le bouton cylindrique
        btn_grad = QRadialGradient(-1, -1 + offset_y, radius)
        btn_grad.setColorAt(0.0, light_c)
        btn_grad.setColorAt(0.7, base_c)
        btn_grad.setColorAt(1.0, dark_c)

        # Ombre d'enfoncement sous le bouton
        if not self.is_pressed:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 70)))
            painter.drawEllipse(QPointF(0, 1.2), radius + 0.5, radius + 0.5)

        painter.setPen(QPen(dark_c, 1))
        painter.setBrush(QBrush(btn_grad))
        painter.drawEllipse(QPointF(0, offset_y), radius, radius)

        # Reflet spéculaire en croissant en haut à gauche
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 160)))
        painter.drawEllipse(QPointF(-2, -2 + offset_y), 1.8, 1.2)

    def mousePressEvent(self, event):
        scene = self.scene()
        if hasattr(scene, "interaction_policy") and not scene.interaction_policy.can_interact(self.component_id):
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton and event.pos().toPoint().manhattanLength() < 12:
            self.is_pressed = True
            self.update()
            self.button_pressed.emit(self.component_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_pressed:
            self.is_pressed = False
            self.update()
            self.button_released.emit(self.component_id)
            event.accept()
            return
        super().mouseReleaseEvent(event)
