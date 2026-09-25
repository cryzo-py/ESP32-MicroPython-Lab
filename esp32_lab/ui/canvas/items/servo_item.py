"""
Rendu graphique ultra-réaliste du micro-servomoteur TowerPro SG90
Boîtier polycarbonate bleu translucide, train d'engrenages interne, palonnier en nylon
orientable avec vis de serrage chromée, et nappe 3 conducteurs (GND, VCC, PWM).
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


class ServoGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un servomoteur SG90 avec son palonnier actif."""

    def __init__(self, component_id: str, angle: float = 90.0, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.angle = max(0.0, min(180.0, float(angle)))

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # Fiche connecteur 3 broches Dupont à l'extrémité du câble plat (GND, VCC, PWM)
        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND (Marron)", parent=self)
        self.pin_gnd.setPos(-16, 42)

        self.pin_vcc = PinAnchorItem(component_id, "vcc", "5V (Rouge)", parent=self)
        self.pin_vcc.setPos(0, 42)

        self.pin_sig = PinAnchorItem(component_id, "sig", "PWM (Orange)", parent=self)
        self.pin_sig.setPos(16, 42)

    def boundingRect(self) -> QRectF:
        return QRectF(-55, -50, 110, 102)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le boîtier
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawRoundedRect(QRectF(-36, -10, 72, 34), 4, 4)

        # 2. Câble ruban 3 fils (Marron, Rouge, Orange) sortant du boîtier
        self._paint_cable_and_header(painter)

        # 3. Boîtier bleu polycarbonate SG90 avec pattes de fixation
        self._paint_servo_casing(painter)

        # 4. Tour de transmission et palonnier rotatif en nylon
        self._paint_horn_and_gears(painter)

    def _paint_cable_and_header(self, painter: QPainter):
        """Nappe plate 3 conducteurs souple avec connecteur Dupont noir à broches."""
        # 3 conducteurs : Marron (-16), Rouge (0), Orange (16)
        wire_colors = [("#78350f", -12), ("#dc2626", 0), ("#ea580c", 12)]

        for color_hex, offset_x in wire_colors:
            wire_path = QPainterPath()
            wire_path.moveTo(offset_x * 0.4, 20)
            wire_path.cubicTo(offset_x * 0.5, 28, offset_x, 32, offset_x, 42)
            painter.setPen(QPen(QColor(color_hex), 4.5, Qt.SolidLine, Qt.RoundCap))
            painter.drawPath(wire_path)

        # Boîtier du connecteur femelle Dupont noir
        header_rect = QRectF(-22, 36, 44, 12)
        painter.setPen(QPen(QColor("#27272a"), 1))
        painter.setBrush(QBrush(QColor("#09090b")))
        painter.drawRoundedRect(header_rect, 1.5, 1.5)

        # 3 alvéoles métalliques dorées où s'insèrent les fils
        for px in [-16, 0, 16]:
            painter.setPen(QPen(QColor("#3f3f46"), 0.6))
            painter.setBrush(QBrush(QColor("#18181b")))
            painter.drawRect(QRectF(px - 3, 39, 6, 6))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawRect(QRectF(px - 1.5, 40.5, 3, 3))

    def _paint_servo_casing(self, painter: QPainter):
        """Boîtier en plastique bleu translucide avec oreilles de fixation."""
        # Pattes de fixation latérales avec œillets métalliques
        flange_grad = QLinearGradient(-48, 0, 48, 0)
        flange_grad.setColorAt(0.0, QColor("#1d4ed8"))
        flange_grad.setColorAt(0.5, QColor("#2563eb"))
        flange_grad.setColorAt(1.0, QColor("#1d4ed8"))

        painter.setPen(QPen(QColor("#1e3a8a"), 1))
        painter.setBrush(QBrush(flange_grad))

        # Flange gauche
        painter.drawRoundedRect(QRectF(-48, -4, 14, 16), 2, 2)
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawEllipse(QPointF(-42, 4), 2.5, 2.5) # Trou d'œillet de vis
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawEllipse(QPointF(-42, 4), 1.5, 1.5)

        # Flange droite
        painter.setBrush(QBrush(flange_grad))
        painter.drawRoundedRect(QRectF(34, -4, 14, 16), 2, 2)
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawEllipse(QPointF(40, 4), 2.5, 2.5)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawEllipse(QPointF(40, 4), 1.5, 1.5)

        # Corps principal bleu translucide
        body_grad = QLinearGradient(-35, -12, 35, 22)
        body_grad.setColorAt(0.0, QColor("#3b82f6"))
        body_grad.setColorAt(0.4, QColor("#2563eb"))
        body_grad.setColorAt(1.0, QColor("#1d4ed8"))

        painter.setPen(QPen(QColor("#1e40af"), 1.2))
        painter.setBrush(QBrush(body_grad))
        painter.drawRoundedRect(QRectF(-35, -12, 70, 32), 3, 3)

        # Silhouettes d'engrenages internes visibles par transparence
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 25)))
        painter.drawEllipse(QPointF(-16, 2), 12, 12)
        painter.drawEllipse(QPointF(6, 4), 9, 9)

        # Sérigraphie TowerPro SG90
        font_logo = QFont("Arial", 6, QFont.Bold)
        painter.setFont(font_logo)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRectF(-35, 4, 70, 10), Qt.AlignCenter, "Tower Pro")
        font_sub = QFont("Arial", 5, QFont.Bold)
        painter.setFont(font_sub)
        painter.setPen(QColor("#bfdbfe"))
        painter.drawText(QRectF(-35, 13, 70, 8), Qt.AlignCenter, f"SG90 · {int(self.angle)}°")

    def _paint_horn_and_gears(self, painter: QPainter):
        """Tour d'axe d'engrenage et palonnier rotatif blanc en nylon orienté selon l'angle."""
        axle_center = QPointF(-16, 0)

        # Tour d'engrenage cylindrique surélevée
        painter.setPen(QPen(QColor("#1e3a8a"), 1))
        painter.setBrush(QBrush(QColor("#1d4ed8")))
        painter.drawEllipse(axle_center, 8, 8)

        # Palonnier en nylon blanc tournant
        painter.save()
        painter.translate(axle_center.x(), axle_center.y())
        # Rotation : 0° = horizontal gauche, 90° = vertical haut, 180° = horizontal droite
        painter.rotate(self.angle - 90.0)

        # Bras du palonnier avec trous d'attache
        horn_path = QPainterPath()
        horn_path.moveTo(-4, 0)
        horn_path.lineTo(-2.5, -30)
        horn_path.arcTo(QRectF(-3.5, -34, 7, 7), 180, -180)
        horn_path.lineTo(4, 0)
        horn_path.arcTo(QRectF(-6, -6, 12, 12), 0, -180)
        horn_path.closeSubpath()

        horn_grad = QLinearGradient(-4, 0, 4, -30)
        horn_grad.setColorAt(0.0, QColor("#fafafa"))
        horn_grad.setColorAt(0.5, QColor("#e2e8f0"))
        horn_grad.setColorAt(1.0, QColor("#cbd5e1"))

        painter.setPen(QPen(QColor("#94a3b8"), 0.8))
        painter.setBrush(QBrush(horn_grad))
        painter.drawPath(horn_path)

        # Perçages dans le palonnier pour tringlerie
        painter.setBrush(QBrush(QColor("#475569")))
        for y_hole in [-10, -17, -24, -30]:
            painter.drawEllipse(QPointF(0, y_hole), 1.0, 1.0)

        # Vis centrale cruciforme chromée
        screw_grad = QRadialGradient(-1, -1, 3.5)
        screw_grad.setColorAt(0.0, QColor("#ffffff"))
        screw_grad.setColorAt(0.7, QColor("#94a3b8"))
        screw_grad.setColorAt(1.0, QColor("#475569"))

        painter.setPen(QPen(QColor("#334155"), 0.6))
        painter.setBrush(QBrush(screw_grad))
        painter.drawEllipse(QPointF(0, 0), 3.5, 3.5)

        # Fente cruciforme
        painter.setPen(QPen(QColor("#1e293b"), 0.8))
        painter.drawLine(QPointF(-2, 0), QPointF(2, 0))
        painter.drawLine(QPointF(0, -2), QPointF(0, 2))

        painter.restore()

    def set_angle(self, angle: float):
        new_angle = max(0.0, min(180.0, float(angle)))
        if self.angle != new_angle:
            self.prepareGeometryChange()
            self.angle = new_angle
            self.update()
