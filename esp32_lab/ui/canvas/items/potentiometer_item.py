"""
Rendu graphique ultra-réaliste d'un potentiomètre rotatif
Corps métallique cylindrique avec collerette filetée, axe cannelé en laiton/aluminium,
index angulaire et 3 broches à œillets en cuivre étamé (VCC, SIG, GND).
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
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


class PotentiometerGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un potentiomètre rotatif de laboratoire."""

    value_changed = Signal(str, int)  # component_id, raw_value (0-4095)

    def __init__(self, component_id: str, raw_value: int = 2048, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.raw_value = max(0, min(4095, int(raw_value)))
        self._is_dragging = False

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 3 broches sous le potentiomètre : VCC (gauche), SIG (centre), GND (droite)
        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VCC (3.3V)", parent=self)
        self.pin_vcc.setPos(-8.5, 32)

        self.pin_sig = PinAnchorItem(component_id, "sig", "SIG (ADC)", parent=self)
        self.pin_sig.setPos(0, 32)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(8.5, 32)

    def boundingRect(self) -> QRectF:
        return QRectF(-28, -28, 56, 68)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le composant
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 55)))
        painter.drawEllipse(QPointF(2, 4), 22, 22)

        # 2. Les 3 pattes métalliques à œillets
        self._paint_terminals(painter)

        # 3. Boîtier cylindrique bleu phénolique
        self._paint_housing(painter)

        # 4. Collerette filetée métallique de montage
        self._paint_threaded_bushing(painter)

        # 5. Axe rotatif moleté avec fente indicatrice d'angle
        self._paint_rotating_shaft(painter)

    def _paint_terminals(self, painter: QPainter):
        """Pattes métalliques à œillets étamées descendant vers le bas."""
        term_grad = QLinearGradient(-1, 0, 1, 0)
        term_grad.setColorAt(0.0, QColor("#64748b"))
        term_grad.setColorAt(0.5, QColor("#f1f5f9"))
        term_grad.setColorAt(1.0, QColor("#475569"))

        painter.setPen(QPen(QColor("#475569"), 0.6))
        painter.setBrush(QBrush(term_grad))

        for px in [-8.5, 0, 8.5]:
            # Patte rectangulaire
            painter.drawRoundedRect(QRectF(px - 2.5, 16, 5, 16), 1, 1)
            # Petit œillet de soudure (trou circulaire)
            painter.setBrush(QBrush(QColor("#1e293b")))
            painter.drawEllipse(QPointF(px, 28), 1.2, 1.2)
            painter.setBrush(QBrush(term_grad))

    def _paint_housing(self, painter: QPainter):
        """Corps rond en plastique bleu industriel ou tôle métallique."""
        house_grad = QRadialGradient(-5, -5, 23)
        house_grad.setColorAt(0.0, QColor("#3b82f6"))
        house_grad.setColorAt(0.7, QColor("#1d4ed8"))
        house_grad.setColorAt(1.0, QColor("#1e3a8a"))

        painter.setPen(QPen(QColor("#172554"), 1.2))
        painter.setBrush(QBrush(house_grad))
        painter.drawEllipse(QPointF(0, 0), 22, 22)

        # Biseau supérieur extérieur
        painter.setPen(QPen(QColor(255, 255, 255, 120), 0.8))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 20.8, 20.8)

    def _paint_threaded_bushing(self, painter: QPainter):
        """Canon fileté métallique en laiton/zinc avec méplat anti-rotation."""
        bush_grad = QLinearGradient(-12, -12, 12, 12)
        bush_grad.setColorAt(0.0, QColor("#f8fafc"))
        bush_grad.setColorAt(0.4, QColor("#cbd5e1"))
        bush_grad.setColorAt(1.0, QColor("#64748b"))

        painter.setPen(QPen(QColor("#475569"), 1))
        painter.setBrush(QBrush(bush_grad))
        painter.drawEllipse(QPointF(0, 0), 14, 14)

        # Filetage circulaire visible
        painter.setPen(QPen(QColor("#94a3b8"), 0.6))
        painter.drawEllipse(QPointF(0, 0), 12.5, 12.5)

    def _paint_rotating_shaft(self, painter: QPainter):
        """Axe cannelé tournant avec encoche blanche de pointage."""
        # Calcul de l'angle : 0 -> -135°, 4095 -> +135° (270° de débattement total)
        angle_deg = -135.0 + (self.raw_value / 4095.0) * 270.0
        angle_rad = math.radians(angle_deg)

        # Axe central en laiton moleté
        shaft_grad = QRadialGradient(-2, -2, 9)
        shaft_grad.setColorAt(0.0, QColor("#fef08a")) # Laiton brillant
        shaft_grad.setColorAt(0.6, QColor("#ca8a04"))
        shaft_grad.setColorAt(1.0, QColor("#713f12"))

        painter.setPen(QPen(QColor("#422006"), 1))
        painter.setBrush(QBrush(shaft_grad))
        painter.drawEllipse(QPointF(0, 0), 9, 9)

        # Fente de réglage pour tournevis (orientée selon l'angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        painter.setPen(QPen(QColor("#ffffff"), 2.2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(0, 0, int(7 * sin_a), int(-7 * cos_a))

        # Flèche / encoche extérieure de repère
        painter.setPen(QPen(QColor("#f8fafc"), 1.8, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(int(10 * sin_a), int(-10 * cos_a), int(13 * sin_a), int(-13 * cos_a))

    def mousePressEvent(self, event):
        scene = self.scene()
        if hasattr(scene, "interaction_policy") and not scene.interaction_policy.can_interact(self.component_id):
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton and event.pos().toPoint().manhattanLength() < 22:
            self._is_dragging = True
            self._update_val_from_mouse(event.pos())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene = self.scene()
        if hasattr(scene, "interaction_policy") and not scene.interaction_policy.can_interact(self.component_id):
            super().mouseMoveEvent(event)
            return

        if self._is_dragging:
            self._update_val_from_mouse(event.pos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _update_val_from_mouse(self, pos: QPointF):
        # Angle polaire par rapport au centre
        deg = math.degrees(math.atan2(pos.x(), -pos.y()))
        deg = max(-135.0, min(135.0, deg))
        ratio = (deg + 135.0) / 270.0
        self.raw_value = int(ratio * 4095)
        self.update()
        self.value_changed.emit(self.component_id, self.raw_value)
