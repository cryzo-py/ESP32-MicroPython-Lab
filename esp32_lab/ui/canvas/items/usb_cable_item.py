"""
Rendu graphique ultra-réaliste d'un câble USB de programmation/alimentation (USB-A vers Micro-USB).
Fiche surmoulée noire avec connecteur métallique inséré dans la carte ESP32,
bague anti-traction et câble souple texturé en courbe de Bézier descendant hors champ.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QGraphicsObject


class USBCableGraphicsItem(QGraphicsObject):
    """Câble USB physique haute fidélité connecté au port USB de la carte ESP32."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setZValue(12)  # Au-dessus des composants pour un rendu réaliste
        self.is_connected = False
        self.setVisible(False)
        self.setAcceptHoverEvents(True)

    def set_connected(self, connected: bool):
        self.is_connected = bool(connected)
        self.setVisible(self.is_connected)
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-25, -20, 70, 200)

    def paint(self, painter: QPainter, option, widget=None):
        if not self.is_connected:
            return

        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée douce sous le connecteur et le câble
        shadow_path = QPainterPath()
        shadow_path.moveTo(0, 0)
        shadow_path.cubicTo(12, 40, 25, 90, 35, 160)

        shadow_pen = QPen(QColor(0, 0, 0, 45), 9.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(shadow_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(shadow_path)

        # 2. Cordon souple noir (Spline Bézier texturé)
        cable_path = QPainterPath()
        cable_path.moveTo(0, 8)
        cable_path.cubicTo(8, 45, 18, 95, 28, 160)

        # Corps principal du câble PVC noir mat
        cable_pen = QPen(QColor("#0f172a"), 7.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(cable_pen)
        painter.drawPath(cable_path)

        # Reflet spéculaire longitudinal le long du câble
        highlight_pen = QPen(QColor("#334155"), 2.2, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(highlight_pen)
        painter.drawPath(cable_path)

        # 3. Manchon anti-pliage (Strain Relief Boot surmoulé)
        boot_rect = QRectF(-6, 2, 12, 16)
        boot_grad = QLinearGradient(-6, 0, 6, 0)
        boot_grad.setColorAt(0.0, QColor("#1e293b"))
        boot_grad.setColorAt(0.4, QColor("#334155"))
        boot_grad.setColorAt(1.0, QColor("#0f172a"))

        painter.setPen(QPen(QColor("#020617"), 0.8))
        painter.setBrush(QBrush(boot_grad))
        painter.drawRoundedRect(boot_rect, 2.5, 2.5)

        # Rainures de flexion sur le manchon
        painter.setPen(QPen(QColor("#0f172a"), 1.0))
        for y_rib in [6, 9, 12]:
            painter.drawLine(QPointF(-4.5, y_rib), QPointF(4.5, y_rib))

        # 4. Fiche surmoulée rectangulaire Micro-USB (Boîtier plastique dur)
        body_rect = QRectF(-8, -12, 16, 15)
        body_grad = QLinearGradient(-8, -12, 8, 3)
        body_grad.setColorAt(0.0, QColor("#334155"))
        body_grad.setColorAt(0.3, QColor("#1e293b"))
        body_grad.setColorAt(0.8, QColor("#0f172a"))
        body_grad.setColorAt(1.0, QColor("#020617"))

        painter.setPen(QPen(QColor("#475569"), 0.8))
        painter.setBrush(QBrush(body_grad))
        painter.drawRoundedRect(body_rect, 2.0, 2.0)

        # Logo USB gravé en relief subtil sur la fiche
        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.drawLine(0, -9, 0, -2)
        painter.drawEllipse(QPointF(0, -9), 1.2, 1.2)
        painter.drawLine(-3, -5, 3, -5)

        # 5. Collerette métallique chromée insérée dans la prise
        metal_rect = QRectF(-5.5, -16, 11, 5)
        metal_grad = QLinearGradient(-5.5, 0, 5.5, 0)
        metal_grad.setColorAt(0.0, QColor("#94a3b8"))
        metal_grad.setColorAt(0.5, QColor("#f1f5f9"))
        metal_grad.setColorAt(1.0, QColor("#64748b"))

        painter.setPen(QPen(QColor("#475569"), 0.6))
        painter.setBrush(QBrush(metal_grad))
        painter.drawRoundedRect(metal_rect, 1.0, 1.0)
