"""
Rendu graphique ultra-réaliste d'un module Relais électromécanique 5V Songle
Boîtier cubique bleu SONGLE SRD-05VDC-SL-C, bornier à vis vert (NO, COM, NC),
optocoupleur, transistor CMS, diodes LED d'état et broches de commande (VCC, GND, IN).
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


class RelayGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un module relais 5V de puissance."""

    def __init__(self, component_id: str, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.is_active = False

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 1. Bornier à vis à gauche : NO (haut), COM (centre), NC (bas)
        self.pin_no = PinAnchorItem(component_id, "no", "NO (Normalement Ouvert)", parent=self)
        self.pin_no.setPos(-40, -16)

        self.pin_com = PinAnchorItem(component_id, "com", "COM (Commun)", parent=self)
        self.pin_com.setPos(-40, 0)

        self.pin_nc = PinAnchorItem(component_id, "nc", "NC (Normalement Fermé)", parent=self)
        self.pin_nc.setPos(-40, 16)

        # 2. Broches de commande à droite : VCC, GND, IN
        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VCC (5V)", parent=self)
        self.pin_vcc.setPos(40, -14)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(40, 0)

        self.pin_in = PinAnchorItem(component_id, "in", "IN (Signal commande)", parent=self)
        self.pin_in.setPos(40, 14)

    def get_anchor_pins(self) -> list[PinAnchorItem]:
        return [c for c in self.childItems() if isinstance(c, PinAnchorItem)]

    def boundingRect(self) -> QRectF:
        return QRectF(-48, -32, 96, 64)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le module
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawRoundedRect(QRectF(-44, -26, 88, 52), 4, 4)

        # 2. PCB support bleu marine
        pcb_grad = QLinearGradient(-44, -26, 44, 26)
        pcb_grad.setColorAt(0.0, QColor("#1e3a8a"))
        pcb_grad.setColorAt(0.5, QColor("#2563eb"))
        pcb_grad.setColorAt(1.0, QColor("#1d4ed8"))

        painter.setPen(QPen(QColor("#1e40af"), 1.2))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(QRectF(-44, -26, 88, 52), 3, 3)

        # 3. Bornier à vis vert (NO, COM, NC) à gauche
        self._paint_screw_terminal(painter)

        # 4. Boîtier cubique bleu du relais SONGLE
        self._paint_relay_cube(painter)

        # 5. LEDs d'état (PWR rouge et RELAY vert)
        self._paint_leds_and_optocoupler(painter)

        # 6. Broches de commande à droite (VCC, GND, IN)
        self._paint_control_pins(painter)

    def _paint_screw_terminal(self, painter: QPainter):
        """Bornier plastique vert à 3 cages de serrage avec vis métalliques."""
        term_rect = QRectF(-44, -24, 18, 48)
        t_grad = QLinearGradient(-44, -24, -26, 24)
        t_grad.setColorAt(0.0, QColor("#16a34a"))
        t_grad.setColorAt(0.5, QColor("#15803d"))
        t_grad.setColorAt(1.0, QColor("#166534"))

        painter.setPen(QPen(QColor("#14532d"), 1))
        painter.setBrush(QBrush(t_grad))
        painter.drawRoundedRect(term_rect, 2, 2)

        # 3 vis métalliques cruciformes avec alvéoles de fil
        screw_y = [-16, 0, 16]
        labels = ["NO", "COM", "NC"]
        font_lbl = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font_lbl)

        for i, py in enumerate(screw_y):
            # Vis métallique argentée
            s_grad = QRadialGradient(-35, py, 4)
            s_grad.setColorAt(0.0, QColor("#ffffff"))
            s_grad.setColorAt(0.6, QColor("#cbd5e1"))
            s_grad.setColorAt(1.0, QColor("#64748b"))

            painter.setPen(QPen(QColor("#475569"), 0.8))
            painter.setBrush(QBrush(s_grad))
            painter.drawEllipse(QPointF(-35, py), 4, 4)

            # Fente de tournevis
            painter.setPen(QPen(QColor("#334155"), 0.8))
            painter.drawLine(QPointF(-37, py), QPointF(-33, py))
            painter.drawLine(QPointF(-35, py - 2), QPointF(-35, py + 2))

            # Sérigraphie blanche du libellé
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRectF(-25, py - 4, 8, 8), Qt.AlignCenter, labels[i])

    def _paint_relay_cube(self, painter: QPainter):
        """Corps cubique bleu emblématique SONGLE SRD-05VDC-SL-C."""
        cube_rect = QRectF(-18, -22, 38, 44)
        c_grad = QLinearGradient(-18, -22, 20, 22)
        c_grad.setColorAt(0.0, QColor("#0284c7"))
        c_grad.setColorAt(0.5, QColor("#0369a1"))
        c_grad.setColorAt(1.0, QColor("#075985"))

        painter.setPen(QPen(QColor("#0c4a6e"), 1.2))
        painter.setBrush(QBrush(c_grad))
        painter.drawRoundedRect(cube_rect, 2, 2)

        # Sérigraphie blanche sur le dessus du relais
        font_brand = QFont("Arial", 6, QFont.Bold)
        painter.setFont(font_brand)
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(QRectF(-18, -19, 38, 9), Qt.AlignCenter, "SONGLE")

        font_model = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font_model)
        painter.setPen(QColor("#e0f2fe"))
        painter.drawText(QRectF(-18, -9, 38, 7), Qt.AlignCenter, "SRD-05VDC-SL-C")
        painter.drawText(QRectF(-18, -1, 38, 6), Qt.AlignCenter, "10A 250VAC · 10A 30VDC")
        painter.drawText(QRectF(-18, 6, 38, 6), Qt.AlignCenter, "10A 125VAC · 28VDC")

        # Schéma mécanique interne du contact sérigraphié
        painter.setPen(QPen(QColor("#bae6fd"), 0.8))
        # Bobine
        painter.drawRect(QRectF(-8, 14, 16, 4))

    def _paint_leds_and_optocoupler(self, painter: QPainter):
        """Optocoupleur EL817 et diodes LED rouge (PWR) et verte (Relay active)."""
        # Optocoupleur noir 4 broches
        painter.setPen(QPen(QColor("#1e293b"), 0.8))
        painter.setBrush(QBrush(QColor("#09090b")))
        painter.drawRoundedRect(QRectF(22, -18, 8, 12), 1, 1)

        # LED PWR (Rouge fixe)
        painter.setBrush(QBrush(QColor("#ef4444")))
        painter.drawRect(QRectF(24, 0, 4, 3))

        # LED Commutation (Verte, allumée si is_active)
        led_c = QColor("#22c55e") if self.is_active else QColor("#14532d")
        painter.setBrush(QBrush(led_c))
        painter.drawRect(QRectF(24, 8, 4, 3))

        if self.is_active:
            glow = QRadialGradient(26, 9.5, 6)
            glow.setColorAt(0.0, QColor(34, 197, 94, 200))
            glow.setColorAt(1.0, QColor(34, 197, 94, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(26, 9.5), 6, 6)

    def _paint_control_pins(self, painter: QPainter):
        """Barrette 3 broches à droite (VCC, GND, IN)."""
        painter.setPen(QPen(QColor("#27272a"), 1))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(QRectF(34, -20, 9, 40), 1.5, 1.5)

        pins_y = [(-14, "VCC"), (0, "GND"), (14, "IN")]
        font_p = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font_p)

        for py, label in pins_y:
            # Alvéole carrée avec contact doré
            painter.setPen(QPen(QColor("#3f3f46"), 0.6))
            painter.setBrush(QBrush(QColor("#09090b")))
            painter.drawRect(QRectF(38.5, py - 2.5, 5, 5))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawRect(QRectF(40, py - 1.2, 2.4, 2.4))

            # Sérigraphie
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRectF(25, py - 4, 12, 8), Qt.AlignRight | Qt.AlignVCenter, label)

    def set_state(self, active: bool):
        if self.is_active != active:
            self.prepareGeometryChange()
            self.is_active = active
            self.update()
