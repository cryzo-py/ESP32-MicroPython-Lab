"""
Rendu graphique ultra-réaliste d'un interrupteur à glissière SPDT (Slide Switch)
Boîtier métallique argenté avec languettes de montage, bouton curseur plastique noir
à crans basculant de gauche à droite et 3 broches de raccordement (1, COM, 2).
"""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PhysicalPinItem


class SlideSwitchGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un interrupteur à glissière traversant SPDT."""
    state_changed = Signal(bool) # True = ON (droite), False = OFF (gauche)

    def __init__(self, component_id: str, is_on: bool = False, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.is_on = bool(is_on)

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 3 broches physiques réelles au pas standard 8.5 px
        # Broche 1 (Gauche), COM (Commun central), Broche 2 (Droite)
        self.pin1 = PhysicalPinItem(component_id, "pin1", "Position 1 (OFF)", pin_length=16.0, pin_thickness=1.6, parent=self)
        self.pin1.setPos(-8.5, 12.0)

        self.pin_com = PhysicalPinItem(component_id, "com", "COM (Commun)", pin_length=16.0, pin_thickness=1.6, parent=self)
        self.pin_com.setPos(0, 12.0)

        self.pin2 = PhysicalPinItem(component_id, "pin2", "Position 2 (ON)", pin_length=16.0, pin_thickness=1.6, parent=self)
        self.pin2.setPos(8.5, 12.0)

    def toggle(self):
        """Bascule l'état de l'interrupteur."""
        self.is_on = not self.is_on
        self.state_changed.emit(self.is_on)
        self.update()

    def set_state(self, state: bool):
        self.is_on = bool(state)
        self.state_changed.emit(self.is_on)
        self.update()

    def mousePressEvent(self, event):
        scene = self.scene()
        if hasattr(scene, "interaction_policy") and not scene.interaction_policy.can_interact(self.component_id):
            super().mousePressEvent(event)
            return

        # Si clic sur le bouton curseur supérieur, basculer la position
        pos = event.pos()
        if QRectF(-14, -14, 28, 14).contains(pos):
            self.toggle()
            event.accept()
            return
        super().mousePressEvent(event)

    def boundingRect(self) -> QRectF:
        return QRectF(-18, -16, 36, 36)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Boîtier métallique argenté / chromé
        case_rect = QRectF(-14, -4, 28, 14)
        case_grad = QLinearGradient(-14, -4, 14, 10)
        case_grad.setColorAt(0.0, QColor("#e2e8f0"))
        case_grad.setColorAt(0.5, QColor("#94a3b8"))
        case_grad.setColorAt(1.0, QColor("#64748b"))
        painter.setPen(QPen(QColor("#475569"), 1.0))
        painter.setBrush(QBrush(case_grad))
        painter.drawRoundedRect(case_rect, 2, 2)

        # Oreilles de fixation métalliques latérales avec rivets
        painter.setPen(QPen(QColor("#475569"), 0.8))
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawRect(QRectF(-17, -1, 3, 8))
        painter.drawRect(QRectF(14, -1, 3, 8))

        # 2. Curseur plastique noir coulissant
        # Position gauche (-5px) ou droite (+5px)
        slider_x = 4.0 if self.is_on else -4.0
        slider_rect = QRectF(slider_x - 4, -12, 8, 10)
        
        slider_grad = QLinearGradient(slider_x - 4, -12, slider_x + 4, -2)
        slider_grad.setColorAt(0.0, QColor("#334155"))
        slider_grad.setColorAt(0.5, QColor("#1e293b"))
        slider_grad.setColorAt(1.0, QColor("#0f172a"))
        painter.setPen(QPen(QColor("#020617"), 1.0))
        painter.setBrush(QBrush(slider_grad))
        painter.drawRoundedRect(slider_rect, 1.5, 1.5)

        # Stries antidérapantes sur le curseur
        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.drawLine(QPointF(slider_x - 2, -9), QPointF(slider_x + 2, -9))
        painter.drawLine(QPointF(slider_x - 2, -6), QPointF(slider_x + 2, -6))

        # 3. Broches métalliques étamées descendantes
        lead_pen = QPen(QColor("#cbd5e1"), 2.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(lead_pen)
        for x_pin in (-8.5, 0, 8.5):
            painter.drawLine(QPointF(x_pin, 10), QPointF(x_pin, 12))

        # 4. Sélection
        if self.isSelected():
            painter.setPen(QPen(QColor("#38bdf8"), 1.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 4, 4)
