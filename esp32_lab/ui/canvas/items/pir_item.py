"""
Rendu graphique ultra-réaliste d'un capteur de mouvement infrarouge PIR (HC-SR501)
Dôme blanc à lentille de Fresnel semi-sphérique, PCB vert sérigraphié avec potentiomètres
de réglage et 3 broches de raccordement (VCC, OUT, GND).
"""

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
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


class PIRGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un module capteur PIR HC-SR501."""

    def __init__(self, component_id: str, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.motion_detected = False

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 3 broches physiques réelles au pas standard 8.5 px
        # VCC (+5V), OUT (Signal logique 3.3V), GND (Masse)
        self.pin_vcc = PhysicalPinItem(component_id, "vcc", "VCC (+5V)", pin_length=18.0, pin_thickness=1.8, parent=self)
        self.pin_vcc.setPos(-8.5, 18.0)

        self.pin_out = PhysicalPinItem(component_id, "out", "OUT (Signal)", pin_length=18.0, pin_thickness=1.8, parent=self)
        self.pin_out.setPos(0, 18.0)

        self.pin_gnd = PhysicalPinItem(component_id, "gnd", "GND (Masse)", pin_length=18.0, pin_thickness=1.8, parent=self)
        self.pin_gnd.setPos(8.5, 18.0)

        # Minuteur pour réinitialiser la détection après un délai
        self._reset_timer = QTimer()
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._on_timeout)

    def trigger_motion(self, duration_ms: int = 3000):
        """Déclenche la détection de mouvement (passe la sortie OUT au niveau HIGH)."""
        self.motion_detected = True
        self.update()
        self._reset_timer.stop()
        self._reset_timer.start(duration_ms)

    def _on_timeout(self):
        self.motion_detected = False
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-22, -22, 44, 46)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. PCB vert de support
        pcb_rect = QRectF(-20, -18, 40, 32)
        pcb_grad = QLinearGradient(-20, -18, 20, 14)
        pcb_grad.setColorAt(0.0, QColor("#15803d"))
        pcb_grad.setColorAt(1.0, QColor("#14532d"))
        painter.setPen(QPen(QColor("#052e16"), 1.0))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(pcb_rect, 3, 3)

        # 2. Deux mini potentiomètres SMD orange/jaune (délai et sensibilité)
        pot_pen = QPen(QColor("#78350f"), 0.6)
        painter.setPen(pot_pen)
        painter.setBrush(QBrush(QColor("#f59e0b")))
        painter.drawRect(QRectF(-17, 4, 6, 6))
        painter.drawRect(QRectF(11, 4, 6, 6))

        # 3. Dôme blanc à lentille de Fresnel (demi-sphère facettée)
        dome_rect = QRectF(-14, -16, 28, 28)
        dome_grad = QRadialGradient(0, -6, 15)
        dome_grad.setColorAt(0.0, QColor("#ffffff"))
        dome_grad.setColorAt(0.6, QColor("#f1f5f9"))
        dome_grad.setColorAt(1.0, QColor("#cbd5e1"))

        painter.setPen(QPen(QColor("#94a3b8"), 1.0))
        painter.setBrush(QBrush(dome_grad))
        painter.drawEllipse(dome_rect)

        # Facettes en nid d'abeille gravées sur la lentille
        painter.setPen(QPen(QColor(203, 213, 225, 180), 0.7))
        painter.drawEllipse(QRectF(-8, -10, 16, 16))
        painter.drawLine(QPointF(-12, -2), QPointF(12, -2))
        painter.drawLine(QPointF(0, -14), QPointF(0, 10))

        # 4. LED témoin de détection (s'allume en rouge vif lors d'un mouvement)
        led_rect = QRectF(-2, 8, 4, 4)
        if self.motion_detected:
            # Halo rouge vif
            halo = QRadialGradient(0, 10, 8)
            halo.setColorAt(0.0, QColor(239, 68, 68, 220))
            halo.setColorAt(1.0, QColor(239, 68, 68, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(halo))
            painter.drawEllipse(QRectF(-8, 2, 16, 16))

            painter.setPen(QPen(QColor("#b91c1c"), 0.8))
            painter.setBrush(QBrush(QColor("#ef4444")))
        else:
            painter.setPen(QPen(QColor("#475569"), 0.6))
            painter.setBrush(QBrush(QColor("#7f1d1d")))
        painter.drawEllipse(led_rect)

        # 5. Broches descendantes
        lead_pen = QPen(QColor("#cbd5e1"), 2.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(lead_pen)
        for x_pin in (-8.5, 0, 8.5):
            painter.drawLine(QPointF(x_pin, 14), QPointF(x_pin, 18))

        # 6. Sélection
        if self.isSelected():
            painter.setPen(QPen(QColor("#38bdf8"), 1.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 4, 4)
