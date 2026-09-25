"""
Rendu graphique ultra-réaliste d'un moteur pas-à-pas unipolaire 28BYJ-48 avec son module driver ULN2003.
Moteur : boîtier métallique cylindrique étamé, pattes de fixation, axe en laiton avec méplat orienté en direct.
Driver : PCB bleu avec CI ULN2003, connecteur moteur 5 broches, 4 LEDs témoins de phases A-B-C-D et bornes IN1..IN4.
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


class StepperMotorGraphicsItem(QGraphicsObject):
    """Moteur pas-à-pas 28BYJ-48 motorisé couplé à sa carte de pilotage ULN2003."""

    def __init__(self, component_id: str, current_angle: float = 0.0, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.angle = float(current_angle)
        self.phase_leds = [False, False, False, False]  # État des bobines A, B, C, D

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 6 broches de commande sur la carte driver ULN2003 :
        # IN1, IN2, IN3, IN4, VCC, GND
        self.pin_in1 = PinAnchorItem(component_id, "in1", "IN1 (Phase A)", parent=self)
        self.pin_in1.setPos(20, 36)

        self.pin_in2 = PinAnchorItem(component_id, "in2", "IN2 (Phase B)", parent=self)
        self.pin_in2.setPos(32, 36)

        self.pin_in3 = PinAnchorItem(component_id, "in3", "IN3 (Phase C)", parent=self)
        self.pin_in3.setPos(44, 36)

        self.pin_in4 = PinAnchorItem(component_id, "in4", "IN4 (Phase D)", parent=self)
        self.pin_in4.setPos(56, 36)

        self.pin_vcc = PinAnchorItem(component_id, "vcc", "5V (VCC Moteur)", parent=self)
        self.pin_vcc.setPos(72, 36)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND (Masse)", parent=self)
        self.pin_gnd.setPos(84, 36)

    def set_step(self, step_index: int, delta_angle: float = 5.625 / 64.0):
        """Met à jour l'étape du pas (0..3 ou 0..7) et fait pivoter l'axe du moteur."""
        self.angle = (self.angle + delta_angle) % 360.0
        # Mettre à jour l'allumage des 4 LEDs de phases
        s = step_index % 4
        self.phase_leds = [s == 0, s == 1, s == 2, s == 3]
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-65, -45, 160, 92)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # ========================================================
        # 1. MOTEUR PAS-À-PAS 28BYJ-48 (Partie gauche, centre ~ -25, 0)
        # ========================================================
        cx_m = -25.0
        cy_m = 0.0

        # Ombre portée du moteur
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawEllipse(QPointF(cx_m + 3, cy_m + 3), 28, 28)

        # Pattes de fixation métalliques latérales
        tab_brush = QBrush(QColor("#94a3b8"))
        painter.setBrush(tab_brush)
        painter.drawRoundedRect(QRectF(cx_m - 34, cy_m - 6, 12, 12), 2, 2)
        painter.drawRoundedRect(QRectF(cx_m + 22, cy_m - 6, 12, 12), 2, 2)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawEllipse(QPointF(cx_m - 28, cy_m), 2.5, 2.5)
        painter.drawEllipse(QPointF(cx_m + 28, cy_m), 2.5, 2.5)

        # Corps cylindrique métallique étamé
        body_grad = QRadialGradient(cx_m - 8, cy_m - 8, 30)
        body_grad.setColorAt(0.0, QColor("#f8fafc"))
        body_grad.setColorAt(0.5, QColor("#cbd5e1"))
        body_grad.setColorAt(0.8, QColor("#94a3b8"))
        body_grad.setColorAt(1.0, QColor("#64748b"))

        painter.setPen(QPen(QColor("#475569"), 1.2))
        painter.setBrush(QBrush(body_grad))
        painter.drawEllipse(QPointF(cx_m, cy_m), 26, 26)

        # Flasque réducteur intérieur
        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawEllipse(QPointF(cx_m, cy_m), 14, 14)

        # Axe rotatif en laiton avec méplat (Tourne selon self.angle)
        painter.save()
        painter.translate(cx_m, cy_m)
        painter.rotate(self.angle)

        shaft_grad = QLinearGradient(-5, -5, 5, 5)
        shaft_grad.setColorAt(0.0, QColor("#fde047"))
        shaft_grad.setColorAt(0.6, QColor("#ca8a04"))
        shaft_grad.setColorAt(1.0, QColor("#854d0e"))

        painter.setPen(QPen(QColor("#713f12"), 0.8))
        painter.setBrush(QBrush(shaft_grad))
        # Forme circulaire avec méplat supérieur
        shaft_path = QPainterPath()
        shaft_path.moveTo(-4, -2)
        shaft_path.lineTo(4, -2)
        shaft_path.arcTo(QRectF(-5, -5, 10, 10), 20, -220)
        shaft_path.closeSubpath()
        painter.drawPath(shaft_path)

        # Repère de rotation sur l'axe
        painter.setPen(QPen(QColor("#451a03"), 1.0))
        painter.drawLine(0, 0, 0, 4)
        painter.restore()

        # ========================================================
        # 2. CARTE DRIVER ULN2003 (Partie droite, centre ~ 52, 0)
        # ========================================================
        # PCB bleu
        driver_rect = QRectF(12, -28, 80, 56)
        pcb_grad = QLinearGradient(12, -28, 92, 28)
        pcb_grad.setColorAt(0.0, QColor("#1e3a8a"))
        pcb_grad.setColorAt(0.6, QColor("#1e40af"))
        pcb_grad.setColorAt(1.0, QColor("#172554"))

        painter.setPen(QPen(QColor("#3b82f6"), 1.0))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(driver_rect, 3, 3)

        # Circuit intégré ULN2003 SO-16 au centre du PCB driver
        ic_rect = QRectF(32, -18, 40, 14)
        painter.setPen(QPen(QColor("#334155"), 0.6))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(ic_rect, 1, 1)

        painter.setFont(QFont("Arial", 4, QFont.Bold))
        painter.setPen(QColor("#e2e8f0"))
        painter.drawText(ic_rect, Qt.AlignCenter, "ULN2003")

        # 4 LEDs témoins de phases A, B, C, D (Rouges)
        led_x_coords = [20, 32, 44, 56]
        for i, lx in enumerate(led_x_coords):
            is_active = self.phase_leds[i] if i < len(self.phase_leds) else False
            led_rect = QRectF(lx - 2, 2, 4, 6)
            if is_active:
                painter.setPen(QPen(QColor("#ef4444"), 0.6))
                painter.setBrush(QBrush(QColor("#f87171")))
                painter.drawRect(led_rect)
                glow = QRadialGradient(lx, 5, 6)
                glow.setColorAt(0.0, QColor(239, 68, 68, 180))
                glow.setColorAt(1.0, QColor(239, 68, 68, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(glow))
                painter.drawEllipse(QPointF(lx, 5), 6, 6)
            else:
                painter.setPen(QPen(QColor("#450a0a"), 0.5))
                painter.setBrush(QBrush(QColor("#7f1d1d")))
                painter.drawRect(led_rect)

            painter.setFont(QFont("Arial", 3, QFont.Bold))
            painter.setPen(QColor("#93c5fd"))
            painter.drawText(QRectF(lx - 4, -8, 8, 8), Qt.AlignCenter, chr(ord('A') + i))

        # Sérigraphie des broches IN1..IN4 et alimentation en bas
        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#fbbf24"))
        pin_names = [("1", 20), ("2", 32), ("3", 44), ("4", 56), ("+", 72), ("-", 84)]
        for lbl, px in pin_names:
            painter.drawText(QRectF(px - 5, 26, 10, 6), Qt.AlignCenter, lbl)
