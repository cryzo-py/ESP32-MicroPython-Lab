"""
Rendu graphique ultra-réaliste d'un avertisseur piézoélectrique (Piezo Buzzer)
Boîtier cylindrique noir mat avec chanfrein, évent acoustique central, repère de polarité (+),
autocollant protecteur et broches métalliques traversantes.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PinAnchorItem


class BuzzerGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un buzzer électromagnétique / piézoélectrique."""

    def __init__(self, component_id: str, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.is_active = False

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # Deux broches métalliques traversantes : Positive (+ à gauche) et Négative (- à droite)
        self.pin_pos = PinAnchorItem(component_id, "pos", "+ (Positif)", parent=self)
        self.pin_pos.setPos(-8.5, 24)

        self.pin_neg = PinAnchorItem(component_id, "neg", "- (GND)", parent=self)
        self.pin_neg.setPos(8.5, 24)

    def boundingRect(self) -> QRectF:
        r = 30 if self.is_active else 24
        return QRectF(-r, -r, 2 * r, 2 * r + 12)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ondes acoustiques si actif
        if self.is_active:
            painter.setPen(QPen(QColor(56, 189, 248, 160), 1.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), 22, 22)
            painter.setPen(QPen(QColor(56, 189, 248, 80), 1.5, Qt.DashLine))
            painter.drawEllipse(QPointF(0, 0), 27, 27)

        # 2. Ombre portée sous le buzzer
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawEllipse(QPointF(2, 3), 18, 18)

        # 3. Broches métalliques descendantes
        self._paint_leads(painter)

        # 4. Boîtier cylindrique plastique noir mat (effet 3D)
        self._paint_body(painter)

        # 5. Évent acoustique central et marquage de polarité (+)
        self._paint_details(painter)

    def _paint_leads(self, painter: QPainter):
        """Pattes métalliques en cuivre étamé argenté."""
        lead_grad = QLinearGradient(-1, 0, 1, 0)
        lead_grad.setColorAt(0.0, QColor("#64748b"))
        lead_grad.setColorAt(0.5, QColor("#f1f5f9"))
        lead_grad.setColorAt(1.0, QColor("#475569"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(lead_grad))

        # Patte positive (+) à gauche
        painter.drawRoundedRect(QRectF(-9.7, 10, 2.4, 14), 0.8, 0.8)
        # Patte négative (-) à droite
        painter.drawRoundedRect(QRectF(7.3, 10, 2.4, 14), 0.8, 0.8)

    def _paint_body(self, painter: QPainter):
        """Corps plastique cylindrique noir mat avec chanfrein périphérique."""
        body_grad = QRadialGradient(-4, -4, 18)
        body_grad.setColorAt(0.0, QColor("#3f3f46"))
        body_grad.setColorAt(0.5, QColor("#27272a"))
        body_grad.setColorAt(0.9, QColor("#18181b"))
        body_grad.setColorAt(1.0, QColor("#09090b"))

        painter.setPen(QPen(QColor("#52525b"), 1))
        painter.setBrush(QBrush(body_grad))
        painter.drawEllipse(QPointF(0, 0), 18, 18)

        # Chanfrein extérieur brillant
        painter.setPen(QPen(QColor(255, 255, 255, 80), 0.8))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 16.5, 16.5)

    def _paint_details(self, painter: QPainter):
        """Évent sonore central et repère de polarité (+)."""
        # Évent acoustique central (cavité noire profonde)
        painter.setPen(QPen(QColor("#3f3f46"), 1))
        painter.setBrush(QBrush(QColor("#000000")))
        painter.drawEllipse(QPointF(0, 0), 4, 4)

        # Repère de polarité "+" en relief blanc au-dessus de la broche positive
        font_plus = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font_plus)
        painter.setPen(QColor("#e4e4e7"))
        painter.drawText(QRectF(-14, -14, 10, 10), Qt.AlignCenter, "+")

    def set_active(self, active: bool, freq: int = 0):
        if self.is_active != active:
            self.prepareGeometryChange()
            self.is_active = active
            self.update()
