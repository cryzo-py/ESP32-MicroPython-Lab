"""
Rendu graphique ultra-réaliste d'un afficheur LCD 16x2 (I2C)
Cadre métallique noir embouti avec pattes de sertissage, dalle LCD STN rétroéclairée,
matrice 16x2 pavés de caractères 5x8 points, adaptateur I2C PCF8574 et 4 broches (GND, VCC, SDA, SCL).
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


class LCDGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un écran LCD 16x2 avec son sac à dos I2C."""

    def __init__(self, component_id: str, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.lines = ["                ", "                "]

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches de l'adaptateur I2C PCF8574 à droite (GND, VCC, SDA, SCL)
        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(68, -15)

        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VCC (5V)", parent=self)
        self.pin_vcc.setPos(68, -5)

        self.pin_sda = PinAnchorItem(component_id, "sda", "SDA", parent=self)
        self.pin_sda.setPos(68, 5)

        self.pin_scl = PinAnchorItem(component_id, "scl", "SCL", parent=self)
        self.pin_scl.setPos(68, 15)

    def boundingRect(self) -> QRectF:
        return QRectF(-75, -36, 150, 72)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous l'écran
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 65)))
        painter.drawRoundedRect(QRectF(-68, -30, 136, 62), 4, 4)

        # 2. PCB principal vert foncé (FR-4)
        self._paint_pcb(painter)

        # 3. Cadre métallique noir embouti avec pattes de fixation
        self._paint_metal_bezel(painter)

        # 4. Dalle LCD STN rétroéclairée (vert-jaune réaliste ou bleu)
        self._paint_lcd_glass(painter)

        # 5. Pavés matriciels de caractères (16 colonnes x 2 lignes)
        self._paint_character_matrix(painter)

        # 6. Adaptateur I2C PCF8574 arrière à droite avec connecteur 4 broches
        self._paint_i2c_backpack(painter)

    def _paint_pcb(self, painter: QPainter):
        """PCB support vert foncé industriel avec pastilles de fixation cuivrées."""
        pcb_grad = QLinearGradient(-70, -32, 70, 32)
        pcb_grad.setColorAt(0.0, QColor("#14532d"))
        pcb_grad.setColorAt(0.5, QColor("#166534"))
        pcb_grad.setColorAt(1.0, QColor("#0f3d20"))

        painter.setPen(QPen(QColor("#15803d"), 1.2))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(QRectF(-70, -32, 140, 64), 3, 3)

        # 4 perçages métallisés aux angles
        for hx, hy in [(-66, -28), (66, -28), (-66, 28), (66, 28)]:
            painter.setPen(QPen(QColor("#d97706"), 0.8))
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawEllipse(QPointF(hx, hy), 2.2, 2.2)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawEllipse(QPointF(hx, hy), 1.2, 1.2)

    def _paint_metal_bezel(self, painter: QPainter):
        """Cadre d'encadrement en tôle emboutie noir mat avec biseau."""
        bezel_rect = QRectF(-60, -25, 114, 50)

        bezel_grad = QLinearGradient(-60, -25, 54, 25)
        bezel_grad.setColorAt(0.0, QColor("#27272a"))
        bezel_grad.setColorAt(0.5, QColor("#18181b"))
        bezel_grad.setColorAt(1.0, QColor("#09090b"))

        painter.setPen(QPen(QColor("#3f3f46"), 1))
        painter.setBrush(QBrush(bezel_grad))
        painter.drawRoundedRect(bezel_rect, 2, 2)

        # 6 pattes métalliques de sertissage repliées
        painter.setBrush(QBrush(QColor("#52525b")))
        for px in [-45, -3, 39]:
            painter.drawRect(QRectF(px, -27, 8, 2))
            painter.drawRect(QRectF(px, 25, 8, 2))

    def _paint_lcd_glass(self, painter: QPainter):
        """Fenêtre en verre LCD avec rétroéclairage vert-jaune ou bleu STN."""
        glass_rect = QRectF(-54, -20, 102, 40)

        # Rétroéclairage vert-jaune LCD classique
        backlight_grad = QLinearGradient(-54, -20, 48, 20)
        backlight_grad.setColorAt(0.0, QColor("#84cc16"))
        backlight_grad.setColorAt(0.5, QColor("#a3e635"))
        backlight_grad.setColorAt(1.0, QColor("#65a30d"))

        painter.setPen(QPen(QColor("#4d7c0f"), 1))
        painter.setBrush(QBrush(backlight_grad))
        painter.drawRect(glass_rect)

    def _paint_character_matrix(self, painter: QPainter):
        """Affiche les 16x2 blocs matriciels et le texte affiché."""
        char_w = 5.8
        char_h = 15.0
        start_x = -51.5
        start_y_line1 = -16.0
        start_y_line2 = 2.0

        # Grille de fond des 16 blocs de caractères (matrice de pixels éteints)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(77, 124, 15, 45)))
        for r_y in [start_y_line1, start_y_line2]:
            for c in range(16):
                cx = start_x + c * (char_w + 0.5)
                painter.drawRect(QRectF(cx, r_y, char_w, char_h))

        # Texte alphanumérique des 2 lignes en pixels noirs
        font = QFont("Consolas", 8, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#14532d")) # Noir verdâtre foncé

        # Ligne 1
        l1 = (self.lines[0] if len(self.lines) > 0 else "")[:16].ljust(16)
        painter.drawText(QRectF(-52, start_y_line1 - 1, 100, char_h + 2), Qt.AlignLeft | Qt.AlignVCenter, l1)

        # Ligne 2
        l2 = (self.lines[1] if len(self.lines) > 1 else "")[:16].ljust(16)
        painter.drawText(QRectF(-52, start_y_line2 - 1, 100, char_h + 2), Qt.AlignLeft | Qt.AlignVCenter, l2)

    def _paint_i2c_backpack(self, painter: QPainter):
        """Module d'interface I2C PCF8574 soudé au dos et dépassant à droite."""
        pack_rect = QRectF(55, -22, 18, 44)
        painter.setPen(QPen(QColor("#1e3a8a"), 1))
        painter.setBrush(QBrush(QColor("#1e40af")))
        painter.drawRoundedRect(pack_rect, 1.5, 1.5)

        # Potentiomètre de contraste bleu miniature
        painter.setBrush(QBrush(QColor("#0284c7")))
        painter.drawRect(QRectF(57, -18, 6, 6))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(QPointF(60, -15), 1.2, 1.2)

        # 4 broches mâles à droite (GND, VCC, SDA, SCL)
        pins_y = [(-15, "GND"), (-5, "VCC"), (5, "SDA"), (15, "SCL")]
        font_p = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font_p)

        for py, label in pins_y:
            # Broche métallique étamée sortant vers la droite
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#e2e8f0")))
            painter.drawRect(QRectF(64, py - 1, 7, 2))

            # Sérigraphie
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRectF(55, py - 4, 8, 8), Qt.AlignLeft | Qt.AlignVCenter, label[0])

    def update_lines(self, lines: list[str]):
        self.lines = list(lines)
        self.update()

    def set_lines(self, lines: list[str]):
        self.update_lines(lines)
