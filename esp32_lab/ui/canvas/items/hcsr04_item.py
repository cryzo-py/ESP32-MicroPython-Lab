"""
Rendu graphique ultra-réaliste du capteur de distance à ultrasons HC-SR04
Deux transducteurs cylindriques en aluminium argenté avec grilles micro-perforées et marquages 'T' et 'R',
résonateur à quartz 4 MHz, PCB bleu, et connecteur 4 broches (VCC, TRIG, ECHO, GND).
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
    QRadialGradient,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PinAnchorItem


class HCSR04GraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un module télémètre ultrasonique HC-SR04."""

    def __init__(self, component_id: str, distance_cm: float = 25.0, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.distance_cm = float(distance_cm)

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches métalliques traversantes en bas (VCC, TRIG, ECHO, GND)
        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VCC (5V)", parent=self)
        self.pin_vcc.setPos(-22.5, 36)

        self.pin_trig = PinAnchorItem(component_id, "trig", "TRIG", parent=self)
        self.pin_trig.setPos(-7.5, 36)

        self.pin_echo = PinAnchorItem(component_id, "echo", "ECHO", parent=self)
        self.pin_echo.setPos(7.5, 36)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(22.5, 36)

    def boundingRect(self) -> QRectF:
        return QRectF(-48, -32, 96, 76)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le capteur
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 55)))
        painter.drawRoundedRect(QRectF(-44, -22, 88, 48), 4, 4)

        # 2. Les 4 broches métalliques descendantes
        self._paint_leads(painter)

        # 3. PCB support bleu marine
        self._paint_pcb(painter)

        # 4. Quartz 4.000 MHz métallique
        self._paint_crystal(painter)

        # 5. Les deux transducteurs cylindriques en aluminium (T et R)
        self._paint_transducers(painter)

        # 6. Sérigraphie et affichage de la distance
        self._paint_labels_and_measure(painter)

    def _paint_leads(self, painter: QPainter):
        """Pattes métalliques en cuivre étamé sortant sous le PCB."""
        lead_grad = QLinearGradient(-1, 0, 1, 0)
        lead_grad.setColorAt(0.0, QColor("#64748b"))
        lead_grad.setColorAt(0.5, QColor("#f1f5f9"))
        lead_grad.setColorAt(1.0, QColor("#475569"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(lead_grad))

        for px in [-20, -7, 7, 20]:
            painter.drawRoundedRect(QRectF(px - 1.2, 22, 2.4, 15), 0.8, 0.8)

    def _paint_pcb(self, painter: QPainter):
        """Circuit imprimé porteur bleu."""
        pcb_grad = QLinearGradient(-44, -22, 44, 24)
        pcb_grad.setColorAt(0.0, QColor("#1e3a8a"))
        pcb_grad.setColorAt(0.5, QColor("#2563eb"))
        pcb_grad.setColorAt(1.0, QColor("#1d4ed8"))

        painter.setPen(QPen(QColor("#1e40af"), 1.2))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(QRectF(-44, -22, 88, 46), 3, 3)

        # 4 trous de fixation aux coins
        for hx, hy in [(-40, -18), (40, -18), (-40, 20), (40, 20)]:
            painter.setPen(QPen(QColor("#d97706"), 0.8))
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawEllipse(QPointF(hx, hy), 2.2, 2.2)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawEllipse(QPointF(hx, hy), 1.2, 1.2)

    def _paint_crystal(self, painter: QPainter):
        """Résonateur à quartz 4 MHz en boîtier métallique HC-49S."""
        crystal_rect = QRectF(-6, -18, 12, 6)
        c_grad = QLinearGradient(-6, -18, 6, -12)
        c_grad.setColorAt(0.0, QColor("#f1f5f9"))
        c_grad.setColorAt(0.5, QColor("#cbd5e1"))
        c_grad.setColorAt(1.0, QColor("#94a3b8"))

        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.setBrush(QBrush(c_grad))
        painter.drawRoundedRect(crystal_rect, 2, 2)

    def _paint_transducers(self, painter: QPainter):
        """Les deux capsules ultrasoniques en aluminium avec grillages micro-perforés."""
        # Capsule gauche : Émetteur T
        self._draw_transducer_can(painter, -22, 1, "T")
        # Capsule droite : Récepteur R
        self._draw_transducer_can(painter, 22, 1, "R")

    def _draw_transducer_can(self, painter: QPainter, cx: float, cy: float, label: str):
        # 1. Joint en caoutchouc noir d'étanchéité
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#09090b")))
        painter.drawEllipse(QPointF(cx, cy), 17.5, 17.5)

        # 2. Cylindre d'aluminium brillant (dégradé métallique)
        can_grad = QRadialGradient(cx - 5, cy - 5, 17)
        can_grad.setColorAt(0.0, QColor("#ffffff"))
        can_grad.setColorAt(0.4, QColor("#e2e8f0"))
        can_grad.setColorAt(0.8, QColor("#94a3b8"))
        can_grad.setColorAt(1.0, QColor("#64748b"))

        painter.setPen(QPen(QColor("#475569"), 1.2))
        painter.setBrush(QBrush(can_grad))
        painter.drawEllipse(QPointF(cx, cy), 16.5, 16.5)

        # 3. Cavité conique intérieure avec grillage à mailles
        painter.setPen(QPen(QColor("#1e293b"), 1))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawEllipse(QPointF(cx, cy), 12.5, 12.5)

        # Grille métallique fine intérieure
        painter.setPen(QPen(QColor("#475569"), 0.6))
        for d in range(-8, 9, 4):
            painter.drawLine(int(cx + d), int(cy - 8), int(cx + d), int(cy + 8))
            painter.drawLine(int(cx - 8), int(cy + d), int(cx + 8), int(cy + d))

        # 4. Marquage 'T' ou 'R' estampillé au centre
        font = QFont("Arial", 8, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRectF(cx - 8, cy - 8, 16, 16), Qt.AlignCenter, label)

    def _paint_labels_and_measure(self, painter: QPainter):
        """Sérigraphie HC-SR04 et affichage de la distance."""
        font_name = QFont("Arial", 5, QFont.Bold)
        painter.setFont(font_name)
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(QRectF(-20, -10, 40, 8), Qt.AlignCenter, "HC-SR04")

        # Badge distance mesurée
        font_dist = QFont("Arial", 6, QFont.Bold)
        painter.setFont(font_dist)
        painter.setPen(QColor("#38bdf8"))
        painter.drawText(QRectF(-20, 8, 40, 10), Qt.AlignCenter, f"{self.distance_cm:.1f} cm")

        # Noms des broches en bas
        font_pin = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font_pin)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRectF(-26, 18, 12, 6), Qt.AlignCenter, "VCC")
        painter.drawText(QRectF(-13, 18, 12, 6), Qt.AlignCenter, "TRIG")
        painter.drawText(QRectF(1, 18, 12, 6), Qt.AlignCenter, "ECHO")
        painter.drawText(QRectF(14, 18, 12, 6), Qt.AlignCenter, "GND")

    def set_distance(self, distance_cm: float):
        self.distance_cm = max(2.0, min(400.0, float(distance_cm)))
        self.update()
