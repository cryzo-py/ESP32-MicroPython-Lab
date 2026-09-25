"""
Rendu graphique ultra-réaliste d'un module centrale inertielle 6 axes MPU-6050 (GY-521).
PCB bleu marine de haute précision, puce QFN MPU-6050 avec repères d'axes X-Y-Z en sérigraphie blanche,
LED témoin d'alimentation rouge, régulateur LDO 3.3V, et broches dorées au pas de 2.54 mm.
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
from PySide6.QtWidgets import QGraphicsObject, QInputDialog

from .pin_item import PinAnchorItem


class MPU6050GraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un module IMU 6-axes MPU-6050 / GY-521."""

    def __init__(self, component_id: str, pitch: float = 0.0, roll: float = 0.0, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.pitch = float(pitch)  # Degrés (-90 à +90)
        self.roll = float(roll)    # Degrés (-180 à +180)
        self.accel_x = 0.0
        self.accel_y = 0.0
        self.accel_z = 1.0  # Gravité standard 1g

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 5 broches principales au pas standard 2.54 mm :
        # VCC, GND, SCL, SDA, INT
        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VCC (3.3V-5V)", parent=self)
        self.pin_vcc.setPos(-30, 32)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(-15, 32)

        self.pin_scl = PinAnchorItem(component_id, "scl", "SCL (I2C Clock)", parent=self)
        self.pin_scl.setPos(0, 32)

        self.pin_sda = PinAnchorItem(component_id, "sda", "SDA (I2C Data)", parent=self)
        self.pin_sda.setPos(15, 32)

        self.pin_int = PinAnchorItem(component_id, "int", "INT (Interruption)", parent=self)
        self.pin_int.setPos(30, 32)

    def boundingRect(self) -> QRectF:
        return QRectF(-38, -34, 76, 76)

    def mouseDoubleClickEvent(self, event):
        """Ouvre un dialogue interactif pour ajuster l'inclinaison (Pitch / Roll)."""
        val, ok = QInputDialog.getDouble(
            None,
            "Inclinaison MPU-6050",
            f"Angle de tangage (Pitch en °) [Actuel: {self.pitch:.1f}°] :",
            self.pitch, -90.0, 90.0, 1
        )
        if ok:
            self.pitch = val
            import math
            rad = math.radians(val)
            self.accel_x = math.sin(rad)
            self.accel_z = math.cos(rad)
            self.update()
        super().mouseDoubleClickEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le module
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawRoundedRect(QRectF(-32, -28, 64, 56), 4, 4)

        # 2. PCB bleu marine GY-521 caractéristique
        pcb_grad = QLinearGradient(-30, -26, 30, 26)
        pcb_grad.setColorAt(0.0, QColor("#1e3a8a"))
        pcb_grad.setColorAt(0.5, QColor("#1d4ed8"))
        pcb_grad.setColorAt(1.0, QColor("#172554"))

        painter.setPen(QPen(QColor("#2563eb"), 1.0))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(QRectF(-30, -26, 60, 54), 3.5, 3.5)

        # 3. Trou de fixation doré à gauche
        painter.setPen(QPen(QColor("#fbbf24"), 0.8))
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawEllipse(QPointF(-22, -18), 2.2, 2.2)

        # 4. Puce QFN-24 InvenSense MPU-6050 au centre
        chip_rect = QRectF(-10, -10, 20, 20)
        chip_grad = QLinearGradient(-10, -10, 10, 10)
        chip_grad.setColorAt(0.0, QColor("#27272a"))
        chip_grad.setColorAt(0.5, QColor("#18181b"))
        chip_grad.setColorAt(1.0, QColor("#09090b"))

        painter.setPen(QPen(QColor("#3f3f46"), 0.8))
        painter.setBrush(QBrush(chip_grad))
        painter.drawRoundedRect(chip_rect, 1.5, 1.5)

        # Point repère broche 1 sur le CI
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#71717a")))
        painter.drawEllipse(QPointF(-7, -7), 1.0, 1.0)

        # Gravure laser MPU-6050
        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#a1a1aa"))
        painter.drawText(chip_rect, Qt.AlignCenter, "MPU\n6050")

        # 5. Sérigraphie des axes d'orientation X, Y
        painter.setPen(QPen(QColor("#f8fafc"), 0.8))
        # Axe X vers la droite
        painter.drawLine(14, -6, 22, -6)
        painter.drawLine(20, -8, 22, -6)
        painter.drawLine(20, -4, 22, -6)
        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.drawText(QRectF(22, -10, 8, 8), Qt.AlignCenter, "X")

        # Axe Y vers le bas
        painter.drawLine(14, -6, 14, 2)
        painter.drawLine(12, 0, 14, 2)
        painter.drawLine(16, 0, 14, 2)
        painter.drawText(QRectF(10, 2, 8, 8), Qt.AlignCenter, "Y")

        # 6. LED d'alimentation CMS rouge en haut à droite
        pwr_pos = QPointF(20, -18)
        painter.setBrush(QBrush(QColor("#ef4444")))
        painter.drawRect(QRectF(pwr_pos.x() - 1.2, pwr_pos.y() - 1.5, 2.4, 3))
        glow = QRadialGradient(pwr_pos, 4)
        glow.setColorAt(0.0, QColor(239, 68, 68, 140))
        glow.setColorAt(1.0, QColor(239, 68, 68, 0))
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(pwr_pos, 4, 4)

        # 7. Étiquettes des broches en bas
        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#fbbf24"))
        pin_labels = [("VCC", -24), ("GND", -12), ("SCL", 0), ("SDA", 12), ("INT", 24)]
        for lbl, x in pin_labels:
            painter.drawText(QRectF(x - 6, 22, 12, 6), Qt.AlignCenter, lbl)
