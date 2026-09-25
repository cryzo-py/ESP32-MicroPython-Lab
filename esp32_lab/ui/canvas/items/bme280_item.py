"""
Rendu graphique ultra-réaliste d'un module capteur environnemental BME280 (I2C / SPI).
PCB violet compact haute finition, boîtier métallique étanche Bosch Sensortec avec orifice d'évent,
sérigraphie dorée, régulateur LDO 3.3V, et 4 broches dorées au pas de 2.54 mm (VIN, GND, SCL, SDA).
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


class BME280GraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un module capteur de pression, humidité et température BME280."""

    def __init__(self, component_id: str, temperature: float = 24.0, humidity: float = 50.0, pressure: float = 1013.25, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        
        # Display state only (controlled by model via EventBus)
        self.display_temperature = float(temperature)
        self.display_humidity = float(humidity)
        self.display_pressure = float(pressure)  # en hPa

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches au pas standard 2.54 mm en bas du module :
        # VIN (3.3V), GND, SCL, SDA
        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VIN (3.3V)", parent=self)
        self.pin_vcc.setPos(-22.5, 30)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(-7.5, 30)

        self.pin_scl = PinAnchorItem(component_id, "scl", "SCL (I2C Clock)", parent=self)
        self.pin_scl.setPos(7.5, 30)

        self.pin_sda = PinAnchorItem(component_id, "sda", "SDA (I2C Data)", parent=self)
        self.pin_sda.setPos(22.5, 30)

    def set_environment(self, temperature: float, humidity: float, pressure: float):
        self.display_temperature = temperature
        self.display_humidity = humidity
        self.display_pressure = pressure
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-32, -32, 64, 72)

    def mouseDoubleClickEvent(self, event):
        """Ouvre un dialogue (Désactivé pour garder la source de vérité dans le modèle backend)"""
        super().mouseDoubleClickEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le PCB
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawRoundedRect(QRectF(-26, -26, 52, 54), 4, 4)

        # 2. PCB violet caractéristique (Finition ENIG or)
        pcb_grad = QLinearGradient(-25, -25, 25, 25)
        pcb_grad.setColorAt(0.0, QColor("#581c87"))
        pcb_grad.setColorAt(0.5, QColor("#6b21a8"))
        pcb_grad.setColorAt(1.0, QColor("#4c1d95"))

        painter.setPen(QPen(QColor("#7e22ce"), 1.0))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(QRectF(-25, -25, 50, 52), 3.5, 3.5)

        # 3. Trous de fixation dorés en haut (gauche et droite)
        painter.setPen(QPen(QColor("#fbbf24"), 0.8))
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawEllipse(QPointF(-18, -18), 2.2, 2.2)
        painter.drawEllipse(QPointF(18, -18), 2.2, 2.2)

        # 4. Boîtier métallique du capteur Bosch Sensortec BME280 au centre
        metal_grad = QLinearGradient(-9, -10, 9, 4)
        metal_grad.setColorAt(0.0, QColor("#f1f5f9"))
        metal_grad.setColorAt(0.5, QColor("#cbd5e1"))
        metal_grad.setColorAt(1.0, QColor("#94a3b8"))

        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.setBrush(QBrush(metal_grad))
        painter.drawRoundedRect(QRectF(-9, -10, 18, 14), 1.5, 1.5)

        # Orifice d'évent barométrique (trou d'échantillonnage de l'air)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawEllipse(QPointF(4, -3), 1.4, 1.4)

        # Gravure laser Bosch
        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#475569"))
        painter.drawText(QRectF(-8, -9, 10, 6), Qt.AlignCenter, "BME")
        painter.drawText(QRectF(-8, -4, 10, 6), Qt.AlignCenter, "280")

        # 5. Composants SMD passifs (résistances de tirage I2C et condensateurs de filtrage)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRect(QRectF(-16, -2, 3, 5))
        painter.drawRect(QRectF(-16, 6, 3, 5))
        painter.drawRect(QRectF(13, -2, 3, 5))

        # Régulateur LDO 3.3V
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(QRectF(-6, 7, 12, 6), 0.8, 0.8)

        # 6. Sérigraphie et valeurs environnementales en temps réel
        painter.setFont(QFont("Consolas", 4, QFont.Bold))
        painter.setPen(QColor("#e9d5ff"))
        painter.drawText(QRectF(-25, 15, 50, 8), Qt.AlignCenter, f"{self.display_temperature:.1f}°C {self.display_humidity:.0f}%")

        # Étiquettes des broches en bas
        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#fbbf24"))
        pin_labels = [("V", -18), ("G", -6), ("CL", 6), ("DA", 18)]
        for lbl, x in pin_labels:
            painter.drawText(QRectF(x - 5, 23, 10, 6), Qt.AlignCenter, lbl)
