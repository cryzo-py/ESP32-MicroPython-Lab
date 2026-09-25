"""
Rendu graphique ultra-réaliste d'un module afficheur 4 digits 7 segments TM1637.
PCB noir mat, 4 afficheurs 7 segments rouge vif haute luminosité avec double point central d'horloge (:),
contrôleur TM1637 SO-20 monté au dos/latéralement, et 4 broches coudées/droites (CLK, DIO, VCC, GND).
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


class TM1637GraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un afficheur digital 4 digits TM1637."""

    # Table des 7 segments (a, b, c, d, e, f, g) pour 0-9 et quelques caractères
    SEGMENTS = {
        '0': [1, 1, 1, 1, 1, 1, 0],
        '1': [0, 1, 1, 0, 0, 0, 0],
        '2': [1, 1, 0, 1, 1, 0, 1],
        '3': [1, 1, 1, 1, 0, 0, 1],
        '4': [0, 1, 1, 0, 0, 1, 1],
        '5': [1, 0, 1, 1, 0, 1, 1],
        '6': [1, 0, 1, 1, 1, 1, 1],
        '7': [1, 1, 1, 0, 0, 0, 0],
        '8': [1, 1, 1, 1, 1, 1, 1],
        '9': [1, 1, 1, 1, 0, 1, 1],
        '-': [0, 0, 0, 0, 0, 0, 1],
        ' ': [0, 0, 0, 0, 0, 0, 0],
        'C': [1, 0, 0, 1, 1, 1, 0],
        'E': [1, 0, 0, 1, 1, 1, 1],
        'H': [0, 1, 1, 0, 1, 1, 1],
        'L': [0, 0, 0, 1, 1, 1, 0],
        'P': [1, 1, 0, 0, 1, 1, 1],
        'O': [1, 1, 1, 1, 1, 1, 0],
    }

    def __init__(self, component_id: str, text: str = "12:00", parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.text = str(text)
        self.show_colon = ":" in self.text

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches au pas 2.54 mm à droite (ou en bas) du module :
        # CLK, DIO, VCC, GND
        self.pin_clk = PinAnchorItem(component_id, "clk", "CLK (Horloge)", parent=self)
        self.pin_clk.setPos(42, -18)

        self.pin_dio = PinAnchorItem(component_id, "dio", "DIO (Données)", parent=self)
        self.pin_dio.setPos(42, -6)

        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VCC (5V)", parent=self)
        self.pin_vcc.setPos(42, 6)

        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND (Masse)", parent=self)
        self.pin_gnd.setPos(42, 18)

    def set_display(self, text: str, colon: bool = True):
        self.text = str(text)
        self.show_colon = colon or (":" in self.text)
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(-52, -30, 106, 60)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le module
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawRoundedRect(QRectF(-48, -26, 96, 52), 4, 4)

        # 2. PCB noir mat haute finition
        pcb_grad = QLinearGradient(-46, -24, 46, 24)
        pcb_grad.setColorAt(0.0, QColor("#1e293b"))
        pcb_grad.setColorAt(0.5, QColor("#0f172a"))
        pcb_grad.setColorAt(1.0, QColor("#020617"))

        painter.setPen(QPen(QColor("#334155"), 1.0))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(QRectF(-46, -24, 92, 48), 3, 3)

        # 4 trous de fixation aux 4 coins du PCB
        painter.setPen(QPen(QColor("#64748b"), 0.6))
        painter.setBrush(QBrush(QColor("#020617")))
        for hx, hy in [(-41, -19), (-41, 19), (34, -19), (34, 19)]:
            painter.drawEllipse(QPointF(hx, hy), 1.8, 1.8)

        # 3. Boîtier des 4 afficheurs 7 segments (Filtre acrylique teinté sombre)
        disp_rect = QRectF(-36, -18, 66, 36)
        painter.setPen(QPen(QColor("#1e1e24"), 1.0))
        painter.setBrush(QBrush(QColor("#09090b")))
        painter.drawRoundedRect(disp_rect, 2, 2)

        # 4. Rendu des 4 chiffres 7 segments
        clean_chars = [c for c in self.text if c != ':']
        clean_chars = (clean_chars + [' '] * 4)[:4]  # Exactement 4 digits

        digit_xs = [-26, -12, 6, 20]
        for i, ch in enumerate(clean_chars):
            self._draw_7segment(painter, digit_xs[i], 0, ch)

        # 5. Deux points de l'horloge au centre (entre digit 2 et digit 3)
        if self.show_colon:
            painter.setPen(Qt.NoPen)
            colon_glow = QRadialGradient(-3, -5, 3)
            colon_glow.setColorAt(0.0, QColor(239, 68, 68, 220))
            colon_glow.setColorAt(1.0, QColor(239, 68, 68, 0))
            painter.setBrush(QBrush(QColor("#ef4444")))
            painter.drawEllipse(QPointF(-3, -5), 1.5, 1.5)
            painter.drawEllipse(QPointF(-3, 5), 1.5, 1.5)

        # 6. Étiquettes des broches à droite
        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#fbbf24"))
        labels = [("CLK", -18), ("DIO", -6), ("VCC", 6), ("GND", 18)]
        for lbl, y in labels:
            painter.drawText(QRectF(28, y - 4, 12, 8), Qt.AlignRight | Qt.AlignVCenter, lbl)

    def _draw_7segment(self, painter: QPainter, cx: float, cy: float, char: str):
        """Dessine un chiffre 7-segments standard rouge avec segments allumés/éteints."""
        segs = self.SEGMENTS.get(str(char).upper(), self.SEGMENTS[' '])
        w = 9.0
        h = 18.0

        # Couleurs allumé vs éteint
        lit_pen = QPen(QColor("#ef4444"), 1.8, Qt.SolidLine, Qt.RoundCap)
        unlit_pen = QPen(QColor("#271212"), 1.8, Qt.SolidLine, Qt.RoundCap)

        # Segments : 0: a (top), 1: b (top-right), 2: c (bottom-right),
        # 3: d (bottom), 4: e (bottom-left), 5: f (top-left), 6: g (center)
        lines = [
            (cx - w/2 + 1, cy - h/2, cx + w/2 - 1, cy - h/2),     # a
            (cx + w/2, cy - h/2 + 1, cx + w/2, cy - 1),           # b
            (cx + w/2, cy + 1, cx + w/2, cy + h/2 - 1),           # c
            (cx - w/2 + 1, cy + h/2, cx + w/2 - 1, cy + h/2),     # d
            (cx - w/2, cy + 1, cx - w/2, cy + h/2 - 1),           # e
            (cx - w/2, cy - h/2 + 1, cx - w/2, cy - 1),           # f
            (cx - w/2 + 1, cy, cx + w/2 - 1, cy),                 # g
        ]

        for is_lit, (x1, y1, x2, y2) in zip(segs, lines):
            painter.setPen(lit_pen if is_lit else unlit_pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
