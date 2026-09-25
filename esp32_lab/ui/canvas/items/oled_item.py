"""
Rendu graphique ultra-réaliste du module écran graphique OLED SSD1306 (128x64 I2C)
PCB support bleu avec perçages de fixation, dalle de verre minéral noir profond avec nappe FPC,
sérigraphie blanche, composants CMS et barrette de connexion 4 broches (GND, VCC, SCL, SDA).
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PinAnchorItem


class OLEDGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'un module OLED SSD1306 0.96 pouce."""

    def __init__(self, component_id: str, width_px: int = 128, height_px: int = 64, parent=None, width: int = None, height: int = None):
        super().__init__(parent)
        self.component_id = component_id
        self.width_px = width if width is not None else width_px
        self.height_px = height if height is not None else height_px
        self.buffer = bytearray((self.width_px * self.height_px) // 8)

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # 4 broches femelles/mâles en haut au pas de 2.54 mm
        # 1: GND, 2: VCC, 3: SCL, 4: SDA
        self.pin_gnd = PinAnchorItem(component_id, "gnd", "GND", parent=self)
        self.pin_gnd.setPos(-24, -38)

        self.pin_vcc = PinAnchorItem(component_id, "vcc", "VCC (3.3V)", parent=self)
        self.pin_vcc.setPos(-8, -38)

        self.pin_scl = PinAnchorItem(component_id, "scl", "SCL", parent=self)
        self.pin_scl.setPos(8, -38)

        self.pin_sda = PinAnchorItem(component_id, "sda", "SDA", parent=self)
        self.pin_sda.setPos(24, -38)

    def boundingRect(self) -> QRectF:
        return QRectF(-48, -48, 96, 92)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le PCB
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.drawRoundedRect(QRectF(-43, -34, 88, 74), 4, 4)

        # 2. PCB support bleu marine (FR-4)
        self._paint_pcb(painter)

        # 3. Barrette de broches en haut avec sérigraphie (GND, VCC, SCL, SDA)
        self._paint_header(painter)

        # 4. Dalle en verre noir minéral de l'écran OLED
        self._paint_glass_panel(painter)

        # 5. Matrice active de pixels cyan lumineux
        self._paint_pixel_matrix(painter)

        # 6. Reflet spéculaire oblique sur la surface en verre
        self._paint_glass_reflection(painter)

    def _paint_pcb(self, painter: QPainter):
        """PCB support bleu avec trous de fixation ENIG dorés."""
        pcb_grad = QLinearGradient(-44, -36, 44, 38)
        pcb_grad.setColorAt(0.0, QColor("#1e3a8a"))
        pcb_grad.setColorAt(0.5, QColor("#1d4ed8"))
        pcb_grad.setColorAt(1.0, QColor("#172554"))

        painter.setPen(QPen(QColor("#1e40af"), 1.2))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(QRectF(-44, -36, 88, 74), 3, 3)

        # Trous de fixation aux 4 coins (pastilles dorées)
        for hx, hy in [(-40, -32), (40, -32), (-40, 34), (40, 34)]:
            painter.setPen(QPen(QColor("#d97706"), 0.8))
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawEllipse(QPointF(hx, hy), 2.5, 2.5)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawEllipse(QPointF(hx, hy), 1.4, 1.4)

    def _paint_header(self, painter: QPainter):
        """Barrette 4 broches plastique noire avec sérigraphie blanche nette."""
        header_rect = QRectF(-30, -42, 60, 9)
        painter.setPen(QPen(QColor("#27272a"), 1))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(header_rect, 1.5, 1.5)

        # Alvéoles et broches
        pins_meta = [(-24, "GND"), (-8, "VCC"), (8, "SCL"), (24, "SDA")]
        font = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font)

        for px, label in pins_meta:
            # Alvéole carrée avec contact doré
            painter.setPen(QPen(QColor("#3f3f46"), 0.6))
            painter.setBrush(QBrush(QColor("#09090b")))
            painter.drawRect(QRectF(px - 2.5, -40.5, 5, 5))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawRect(QRectF(px - 1.2, -39.2, 2.4, 2.4))

            # Sérigraphie en dessous
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRectF(px - 8, -32, 16, 6), Qt.AlignCenter, label)

    def _paint_glass_panel(self, painter: QPainter):
        """Dalle de verre noir brillant avec biseau et nappe flexible FPC."""
        glass_rect = QRectF(-38, -25, 76, 56)

        # Nappe FPC cuivrée en bas
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#b45309")))
        painter.drawRect(QRectF(-16, 28, 32, 6))

        # Dalle en verre noir minéral profond
        painter.setPen(QPen(QColor("#27272a"), 1))
        painter.setBrush(QBrush(QColor("#09090b")))
        painter.drawRoundedRect(glass_rect, 2, 2)

        # Bordure de verre extérieure
        painter.setPen(QPen(QColor("#18181b"), 1.2))
        painter.drawRect(QRectF(-35, -22, 70, 48))

    def _paint_pixel_matrix(self, painter: QPainter):
        """Zone active de 128x64 pixels projetée dans un rectangle de 64x32 mm."""
        display_rect = QRectF(-32, -18, 64, 40)

        # Fond d'écran OLED éteint (noir bleuté très sombre)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#020617")))
        painter.drawRect(display_rect)

        # Convertir le buffer en QImage matricielle
        img = QImage(self.width_px, self.height_px, QImage.Format_ARGB32)
        img.fill(0)

        color_on = QColor("#38bdf8").rgba() # Cyan lumineux vif

        if getattr(self, "matrix", None):
            for y, row in enumerate(self.matrix):
                if y >= self.height_px:
                    break
                for x, val in enumerate(row):
                    if x >= self.width_px:
                        break
                    if val:
                        img.setPixel(x, y, color_on)
        elif self.buffer:
            for page in range(self.height_px // 8):
                for x in range(self.width_px):
                    idx = page * self.width_px + x
                    if idx < len(self.buffer):
                        byte_val = self.buffer[idx]
                        if byte_val != 0:
                            for b in range(8):
                                if (byte_val >> b) & 1:
                                    y = page * 8 + b
                                    if y < self.height_px:
                                        img.setPixel(x, y, color_on)

        painter.drawImage(display_rect, img)

    def _paint_glass_reflection(self, painter: QPainter):
        """Éclat de réflexion de lumière spéculaire sur la surface du verre."""
        ref_path = QPainterPath()
        ref_path.moveTo(-36, -24)
        ref_path.lineTo(-12, -24)
        ref_path.lineTo(-36, 12)
        ref_path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 22)))
        painter.drawPath(ref_path)

    def update_buffer(self, width: int, height: int, new_buffer: bytes):
        """Met  jour le buffer d'affichage."""
        self.width_px = width
        self.height_px = height
        if isinstance(new_buffer, (bytes, bytearray)):
            self.buffer = bytearray(new_buffer)
            self.matrix = None
        self.update()
