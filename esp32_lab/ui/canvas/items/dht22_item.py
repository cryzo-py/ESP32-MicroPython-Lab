"""
Rendu graphique ultra-réaliste du capteur d'ambiance DHT22 (AM2302)
Boîtier blanc ajouré avec ouïes de ventilation, substrat polymère hygrométrique visible,
onglet supérieur de fixation et 4 broches métalliques (VCC, DATA, NC, GND).
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PinAnchorItem


class DHT22GraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un capteur numérique DHT22 / AM2302."""

    def __init__(self, component_id: str, temperature: float = 24.0, humidity: float = 55.0, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.temperature = float(temperature)
        self.humidity = float(humidity)

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches métalliques traversantes en bas au pas de 2.54 mm
        # 1: VCC, 2: DATA, 3: NC, 4: GND
        self.pin_vcc = PinAnchorItem(component_id, "vcc", "1: VCC (3.3V-5V)", parent=self)
        self.pin_vcc.setPos(-12.75, 44)

        self.pin_data = PinAnchorItem(component_id, "data", "2: DATA", parent=self)
        self.pin_data.setPos(-4.25, 44)

        self.pin_nc = PinAnchorItem(component_id, "nc", "3: NC", parent=self)
        self.pin_nc.setPos(4.25, 44)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "4: GND", parent=self)
        self.pin_gnd.setPos(12.75, 44)

    def boundingRect(self) -> QRectF:
        return QRectF(-30, -32, 60, 84)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le boîtier
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawRoundedRect(QRectF(-24, -20, 50, 54), 4, 4)

        # 2. Les 4 broches métalliques étamées descendantes
        self._paint_leads(painter)

        # 3. Onglet supérieur de fixation murale avec trou de vis
        self._paint_mounting_tab(painter)

        # 4. Boîtier blanc ABS avec ouïes de ventilation ajourées
        self._paint_body_and_grill(painter)

        # 5. Marquage DHT22 et affichage des mesures en temps réel
        self._paint_measurements(painter)

    def _paint_leads(self, painter: QPainter):
        """4 broches dorées/argentées émergeant sous le boîtier."""
        lead_grad = QLinearGradient(-1, 0, 1, 0)
        lead_grad.setColorAt(0.0, QColor("#64748b"))
        lead_grad.setColorAt(0.5, QColor("#f1f5f9"))
        lead_grad.setColorAt(1.0, QColor("#475569"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(lead_grad))

        for px in [-12.75, -4.25, 4.25, 12.75]:
            painter.drawRoundedRect(QRectF(px - 1.2, 30, 2.4, 15), 0.8, 0.8)

    def _paint_mounting_tab(self, painter: QPainter):
        """Languette supérieure moulée pour vis de fixation M3."""
        tab_grad = QLinearGradient(-8, -28, 8, -18)
        tab_grad.setColorAt(0.0, QColor("#ffffff"))
        tab_grad.setColorAt(1.0, QColor("#e2e8f0"))

        painter.setPen(QPen(QColor("#cbd5e1"), 1))
        painter.setBrush(QBrush(tab_grad))

        tab_path = QPainterPath()
        tab_path.moveTo(-8, -18)
        tab_path.lineTo(-8, -24)
        tab_path.arcTo(QRectF(-8, -28, 16, 8), 180, -180)
        tab_path.lineTo(8, -18)
        tab_path.closeSubpath()
        painter.drawPath(tab_path)

        # Trou de fixation
        painter.setBrush(QBrush(QColor("#475569")))
        painter.drawEllipse(QPointF(0, -23), 2.2, 2.2)

    def _paint_body_and_grill(self, painter: QPainter):
        """Corps principal en plastique blanc avec rainures d'aération."""
        body_grad = QLinearGradient(-24, -18, 24, 32)
        body_grad.setColorAt(0.0, QColor("#ffffff"))
        body_grad.setColorAt(0.5, QColor("#f8fafc"))
        body_grad.setColorAt(1.0, QColor("#e2e8f0"))

        painter.setPen(QPen(QColor("#cbd5e1"), 1.2))
        painter.setBrush(QBrush(body_grad))
        painter.drawRoundedRect(QRectF(-24, -18, 48, 50), 3, 3)

        # Fentes de ventilation horizontales (laissant voir l'élément sensible vert/bleu)
        painter.setPen(Qt.NoPen)
        start_y = -10
        for i in range(5):
            fy = start_y + i * 5
            # Cavité de la fente
            painter.setBrush(QBrush(QColor("#0f172a")))
            painter.drawRoundedRect(QRectF(-18, fy, 36, 2.5), 1, 1)
            # Élément capacitif visible au fond
            painter.setBrush(QBrush(QColor("#0284c7")))
            painter.drawRect(QRectF(-14, fy + 0.6, 28, 1.3))

    def _paint_measurements(self, painter: QPainter):
        """Sérigraphie du modèle et valeurs mesurées."""
        font_model = QFont("Arial", 6, QFont.Bold)
        painter.setFont(font_model)
        painter.setPen(QColor("#475569"))
        painter.drawText(QRectF(-24, 15, 48, 8), Qt.AlignCenter, "DHT22 / AM2302")

        # Badge de mesure dynamique
        font_data = QFont("Arial", 5, QFont.Bold)
        painter.setFont(font_data)
        painter.setPen(QColor("#0284c7"))
        painter.drawText(QRectF(-24, 23, 48, 8), Qt.AlignCenter, f"{self.temperature:.1f}°C  {self.humidity:.0f}%")

    def set_values(self, temp: float, hum: float):
        self.temperature = float(temp)
        self.humidity = float(hum)
        self.update()
