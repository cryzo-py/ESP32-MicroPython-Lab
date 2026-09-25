"""
Rendu graphique ultra-réaliste d'une photorésistance (LDR / Photoresistor)
Disque céramique beige avec piste sinueuse en sulfure de cadmium (CdS),
résine époxy transparente et pattes traversantes pour platine d'expérimentation.
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


class LDRGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'une photorésistance LDR 5mm."""

    def __init__(self, component_id: str, lux: float = 300.0, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.lux = max(0.0, float(lux))

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # Deux broches physiques réelles espacées de 2 pas (17.0 mm / pixels)
        self.pin1 = PhysicalPinItem(component_id, "pin1", "Broche 1 (LDR)", pin_length=20.0, pin_thickness=1.6, parent=self)
        self.pin1.setPos(0, -8.5)

        self.pin2 = PhysicalPinItem(component_id, "pin2", "Broche 2 (LDR)", pin_length=20.0, pin_thickness=1.6, parent=self)
        self.pin2.setPos(0, 8.5)

    @property
    def resistance_value(self) -> float:
        """Calcule la résistance équivalente approximative en Ohms selon l'éclairement en Lux."""
        # Obscurité (0 Lux) ~ 1 MΩ, Plein soleil (1000 Lux) ~ 400 Ω
        if self.lux <= 0:
            return 1_000_000.0
        return max(200.0, 500_000.0 / (self.lux + 5.0))

    def boundingRect(self) -> QRectF:
        return QRectF(-16, -24, 32, 48)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Pattes métalliques étamées sous le disque
        lead_pen = QPen(QColor("#cbd5e1"), 2.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(lead_pen)
        if not self.pin1.is_inserted:
            painter.drawLine(QPointF(0, -6), QPointF(0, -8.5))
        if not self.pin2.is_inserted:
            painter.drawLine(QPointF(0, 6), QPointF(0, 8.5))

        # 2. Base céramique beige/orangée (disque principal)
        disc_rect = QRectF(-12, -12, 24, 24)
        base_grad = QRadialGradient(0, -2, 14)
        base_grad.setColorAt(0.0, QColor("#fed7aa"))
        base_grad.setColorAt(0.7, QColor("#fb923c"))
        base_grad.setColorAt(1.0, QColor("#c2410c"))

        painter.setPen(QPen(QColor("#9a3412"), 1.2))
        painter.setBrush(QBrush(base_grad))
        painter.drawEllipse(disc_rect)

        # 3. Pistes sinueuses en serpentin (Sulfure de Cadmium - CdS)
        cds_pen = QPen(QColor("#7c2d12"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(cds_pen)
        
        path = QPainterPath()
        path.moveTo(-7, -6)
        path.lineTo(6, -6)
        path.lineTo(6, -2)
        path.lineTo(-6, -2)
        path.lineTo(-6, 2)
        path.lineTo(6, 2)
        path.lineTo(6, 6)
        path.lineTo(-7, 6)
        painter.drawPath(path)

        # 4. Traces conductrices argentées des électrodes
        silver_pen = QPen(QColor("#e2e8f0"), 1.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(silver_pen)
        painter.drawLine(QPointF(-8, -6), QPointF(-4, -6))
        painter.drawLine(QPointF(-8, 6), QPointF(-4, 6))

        # 5. Dôme de protection translucide (reflet spéculaire)
        shine_grad = QLinearGradient(-8, -10, 4, 4)
        shine_grad.setColorAt(0.0, QColor(255, 255, 255, 140))
        shine_grad.setColorAt(0.4, QColor(255, 255, 255, 40))
        shine_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shine_grad))
        painter.drawEllipse(QRectF(-10, -10, 20, 14))

        # 6. Indicateur de sélection
        if self.isSelected():
            painter.setPen(QPen(QColor("#38bdf8"), 1.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 4, 4)
