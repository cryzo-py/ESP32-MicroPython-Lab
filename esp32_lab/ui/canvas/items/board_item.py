"""
Rendu graphique ultra-réaliste de la carte ESP32-WROOM-32 DevKit V1
PCB noir mat satiné, blindage métallique gravé au laser, antenne méandre dorée,
connecteur USB métallique, boutons poussoirs CMS, régulateur AMS1117, barrettes de broches physiques.
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

from ....core.models.board import ESP32DevKitProfile, create_esp32_devkit_profile
from .pin_item import PhysicalPinItem, PinAnchorItem


class BoardGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'une véritable carte de développement ESP32."""

    def __init__(self, board_id: str = "esp32", parent=None):
        super().__init__(parent)
        self.board_id = board_id
        self.component_id = board_id
        self.profile: ESP32DevKitProfile = create_esp32_devkit_profile()
        self.width = self.profile.width   # 110.0 px
        self.height = self.profile.height # 180.0 px
        self.pin_anchors: dict[str, PinAnchorItem] = {}
        self.gpio2_led_state = False
        self.is_powered = False

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setTransformOriginPoint(self.width / 2.0, self.height / 2.0)
        self.setZValue(3)

        self._setup_pins()

    def set_powered(self, powered: bool):
        if self.is_powered != powered:
            self.is_powered = bool(powered)
            self.update()

    def get_usb_socket_scene_pos(self) -> QPointF:
        """Retourne la position globale du port Micro-USB au bas de la carte."""
        cx = self.width / 2.0
        return self.mapToScene(QPointF(cx, self.height - 2.0))

    def _setup_pins(self):
        cx = self.width / 2.0
        cy = self.height / 2.0

        for pin in self.profile.pins.values():
            anchor = PhysicalPinItem(
                owner_id=self.board_id,
                pin_id=pin.pin_id,
                pin_name=pin.label,
                pin_length=pin.pin_length,
                pin_thickness=pin.pin_thickness,
                parent=self,
            )
            anchor.gpio_num = pin.gpio_num
            anchor.role = pin.role
            anchor.description = pin.description
            anchor.setPos(cx + pin.rel_x, cy + pin.rel_y)

            # Registre principal (ex: "GPIO2", "EN", "VIN", "GND_1")
            self.pin_anchors[pin.pin_id] = anchor

            # Alias pour flexibilité et rétrocompatibilité
            if pin.gpio_num is not None:
                self.pin_anchors[f"GPIO{pin.gpio_num}"] = anchor
                self.pin_anchors[f"IO{pin.gpio_num}"] = anchor
                self.pin_anchors[str(pin.gpio_num)] = anchor
            if pin.label == "GND":
                if "GND" not in self.pin_anchors:
                    self.pin_anchors["GND"] = anchor
            elif pin.label == "3V3":
                self.pin_anchors["3V3"] = anchor
                self.pin_anchors["3.3V"] = anchor
            elif pin.label == "VIN":
                self.pin_anchors["VIN"] = anchor
                self.pin_anchors["5V"] = anchor

    def get_pin_anchor(self, pin_id: str | int) -> PinAnchorItem | None:
        """Recherche une broche physique par identifiant universel, label ou numéro GPIO."""
        p = self.profile.get_pin(pin_id)
        if p and p.pin_id in self.pin_anchors:
            return self.pin_anchors[p.pin_id]
        return self.pin_anchors.get(str(pin_id))

    def boundingRect(self) -> QRectF:
        return QRectF(-6, -6, self.width + 12, self.height + 16)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le PCB
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 70)))
        painter.drawRoundedRect(QRectF(3, 4, self.width, self.height), 7, 7)

        # 2. PCB Noir mat satiné avec chanfrein
        pcb_grad = QLinearGradient(0, 0, self.width, self.height)
        pcb_grad.setColorAt(0.0, QColor("#1e1e24"))
        pcb_grad.setColorAt(0.5, QColor("#141417"))
        pcb_grad.setColorAt(1.0, QColor("#0d0d10"))

        painter.setPen(QPen(QColor("#2c2c34"), 1.5))
        painter.setBrush(QBrush(pcb_grad))
        painter.drawRoundedRect(0, 0, self.width, self.height, 6, 6)

        # 3. Trous de fixation aux 4 coins (pastilles dorées ENIG)
        self._paint_mounting_holes(painter)

        # 4. Antenne PCB méandre dorée en haut
        self._paint_antenna(painter)

        # 5. Boîtier de blindage RF ESP-WROOM-32 (métal brossé gravé)
        self._paint_rf_shield(painter)

        # 6. Port USB métallique au bas
        self._paint_usb_port(painter)

        # 7. Boutons poussoirs EN et BOOT
        self._paint_buttons(painter)

        # 8. Puce convertisseur UART CP2102 et Régulateur AMS1117
        self._paint_ics(painter)

        # 9. Diodes LED CMS (Alimentation rouge & GPIO 2 bleue)
        self._paint_leds(painter)

        # 10. Barrettes de broches femelles/mâles et sérigraphie blanche
        self._paint_headers_and_silkscreen(painter)

    def _paint_mounting_holes(self, painter: QPainter):
        hole_coords = [(8, 8), (self.width - 8, 8), (8, self.height - 8), (self.width - 8, self.height - 8)]
        for hx, hy in hole_coords:
            painter.setPen(QPen(QColor("#d97706"), 1))
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawEllipse(QPointF(hx, hy), 3.5, 3.5)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawEllipse(QPointF(hx, hy), 2.0, 2.0)

    def _paint_antenna(self, painter: QPainter):
        """Dessine l'antenne méandre PCB caractéristique en haut du module."""
        cx = self.width / 2.0
        ant_rect = QRectF(cx - 28, 6, 56, 17)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#0a0a0c")))
        painter.drawRoundedRect(ant_rect, 2, 2)

        pen_gold = QPen(QColor("#eab308"), 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        painter.setPen(pen_gold)

        path = QPainterPath()
        path.moveTo(cx - 24, 19)
        path.lineTo(cx - 24, 10)
        path.lineTo(cx + 24, 10)
        for x in [cx - 16, cx - 8, cx, cx + 8, cx + 16]:
            path.moveTo(x, 10)
            path.lineTo(x, 18)
            path.lineTo(x + 4, 18)
            path.lineTo(x + 4, 10)
        painter.drawPath(path)

    def _paint_rf_shield(self, painter: QPainter):
        """Boîtier de blindage métallique nickelé avec sérigraphie laser."""
        cx = self.width / 2.0
        shield_rect = QRectF(cx - 34, 27, 68, 68)

        metal_grad = QLinearGradient(cx - 34, 27, cx + 34, 95)
        metal_grad.setColorAt(0.0, QColor("#e2e8f0"))
        metal_grad.setColorAt(0.3, QColor("#cbd5e1"))
        metal_grad.setColorAt(0.7, QColor("#94a3b8"))
        metal_grad.setColorAt(1.0, QColor("#cbd5e1"))

        painter.setPen(QPen(QColor("#64748b"), 1.0))
        painter.setBrush(QBrush(metal_grad))
        painter.drawRoundedRect(shield_rect, 3, 3)

        painter.setPen(QPen(QColor(255, 255, 255, 180), 0.8))
        painter.drawLine(cx - 32, 29, cx + 32, 29)
        painter.drawLine(cx - 32, 29, cx - 32, 93)

        font_brand = QFont("Arial", 6, QFont.Bold)
        painter.setFont(font_brand)
        painter.setPen(QColor("#334155"))
        painter.drawText(QRectF(cx - 34, 34, 68, 12), Qt.AlignCenter, "ESPRESSIF")

        font_model = QFont("Arial", 5, QFont.Bold)
        painter.setFont(font_model)
        painter.drawText(QRectF(cx - 34, 48, 68, 10), Qt.AlignCenter, "ESP-WROOM-32")

        font_fcc = QFont("Arial", 3, QFont.Normal)
        painter.setFont(font_fcc)
        painter.setPen(QColor("#475569"))
        painter.drawText(QRectF(cx - 34, 62, 68, 8), Qt.AlignCenter, "FCC ID: 2AC7Z-ESPWROOM32")
        painter.drawText(QRectF(cx - 34, 72, 68, 8), Qt.AlignCenter, "CE  RoHS")

    def _paint_usb_port(self, painter: QPainter):
        """Prise Micro-USB métallique réaliste avec pattes de soudure et cavité."""
        cx = self.width / 2.0
        usb_rect = QRectF(cx - 12, self.height - 13, 24, 16)

        usb_grad = QLinearGradient(cx - 12, self.height - 13, cx + 12, self.height + 3)
        usb_grad.setColorAt(0.0, QColor("#e2e8f0"))
        usb_grad.setColorAt(0.5, QColor("#cbd5e1"))
        usb_grad.setColorAt(1.0, QColor("#94a3b8"))

        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.setBrush(QBrush(usb_grad))
        painter.drawRoundedRect(usb_rect, 2, 2)

        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRoundedRect(QRectF(cx - 9, self.height - 2, 18, 4), 1, 1)

        painter.setBrush(QBrush(QColor("#94a3b8")))
        painter.drawRect(QRectF(cx - 14, self.height - 10, 3, 6))
        painter.drawRect(QRectF(cx + 11, self.height - 10, 3, 6))

    def _paint_buttons(self, painter: QPainter):
        """Boutons poussoirs miniatures SMD EN et BOOT."""
        self._draw_smd_button(painter, 16, self.height - 24, "EN")
        self._draw_smd_button(painter, self.width - 25, self.height - 24, "BOOT")

    def _draw_smd_button(self, painter: QPainter, x: float, y: float, label: str):
        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawRoundedRect(QRectF(x, y, 9, 9), 1.5, 1.5)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawEllipse(QPointF(x + 4.5, y + 4.5), 2.5, 2.5)

        font = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(QRectF(x - 3, y - 7, 15, 7), Qt.AlignCenter, label)

    def _paint_ics(self, painter: QPainter):
        """Circuit intégré USB-UART CP2102 et régulateur AMS1117."""
        cx = self.width / 2.0

        # CP2102
        qfn_rect = QRectF(cx - 8, 100, 16, 16)
        painter.setPen(QPen(QColor("#334155"), 0.6))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(qfn_rect, 1, 1)

        painter.setBrush(QBrush(QColor("#475569")))
        painter.drawEllipse(QPointF(cx - 5, 103), 0.8, 0.8)

        # AMS1117
        reg_rect = QRectF(cx - 10, 122, 20, 13)
        painter.setBrush(QBrush(QColor("#1e293b")))
        painter.drawRoundedRect(reg_rect, 1, 1)
        painter.setBrush(QBrush(QColor("#94a3b8")))
        painter.drawRect(QRectF(cx - 7, 120, 14, 2.5))

    def _paint_leds(self, painter: QPainter):
        """LEDs SMD d'alimentation (PWR) et GPIO 2."""
        cx = self.width / 2.0

        # 1. LED PWR (s'allume uniquement si la carte est alimentée)
        pwr_pos = QPointF(cx - 13, 142)
        if self.is_powered:
            painter.setPen(QPen(QColor("#450a0a"), 0.5))
            painter.setBrush(QBrush(QColor("#ef4444")))
            painter.drawRect(QRectF(pwr_pos.x() - 1.5, pwr_pos.y() - 2.5, 3, 5))

            glow_pwr = QRadialGradient(pwr_pos, 6)
            glow_pwr.setColorAt(0.0, QColor(239, 68, 68, 180))
            glow_pwr.setColorAt(1.0, QColor(239, 68, 68, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow_pwr))
            painter.drawEllipse(pwr_pos, 6, 6)
        else:
            painter.setPen(QPen(QColor("#260505"), 0.5))
            painter.setBrush(QBrush(QColor("#450a0a")))
            painter.drawRect(QRectF(pwr_pos.x() - 1.5, pwr_pos.y() - 2.5, 3, 5))

        font = QFont("Arial", 3, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#e2e8f0"))
        painter.drawText(QRectF(pwr_pos.x() - 6, pwr_pos.y() + 3.5, 12, 5), Qt.AlignCenter, "PWR")

        # 2. LED GPIO 2
        io2_pos = QPointF(cx + 13, 142)
        if self.gpio2_led_state:
            painter.setPen(QPen(QColor("#1e3a8a"), 0.5))
            painter.setBrush(QBrush(QColor("#38bdf8")))
            painter.drawRect(QRectF(io2_pos.x() - 1.5, io2_pos.y() - 2.5, 3, 5))

            glow_io2 = QRadialGradient(io2_pos, 8)
            glow_io2.setColorAt(0.0, QColor(56, 189, 248, 220))
            glow_io2.setColorAt(0.5, QColor(2, 132, 199, 100))
            glow_io2.setColorAt(1.0, QColor(2, 132, 199, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow_io2))
            painter.drawEllipse(io2_pos, 8, 8)
        else:
            painter.setPen(QPen(QColor("#1e293b"), 0.5))
            painter.setBrush(QBrush(QColor("#0f172a")))
            painter.drawRect(QRectF(io2_pos.x() - 1.5, io2_pos.y() - 2.5, 3, 5))

        painter.setPen(QColor("#e2e8f0"))
        painter.drawText(QRectF(io2_pos.x() - 6, io2_pos.y() + 3.5, 12, 5), Qt.AlignCenter, "IO2")

    def _paint_headers_and_silkscreen(self, painter: QPainter):
        """Barrettes de broches plastiques avec alvéoles dorées et sérigraphies blanches."""
        cx = self.width / 2.0
        cy = self.height / 2.0
        font_pin = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font_pin)

        # Corps plastique des barrettes
        painter.setPen(QPen(QColor("#27272a"), 0.8))
        painter.setBrush(QBrush(QColor("#18181b")))
        # Rangée gauche (centrée sur cx - 44.5 = 10.5)
        painter.drawRoundedRect(QRectF(cx - 44.5 - 4.5, 23, 9, 134), 2, 2)
        # Rangée droite (centrée sur cx + 44.5 = 99.5)
        painter.drawRoundedRect(QRectF(cx + 44.5 - 4.5, 23, 9, 134), 2, 2)

        for pin in self.profile.pins.values():
            px = cx + pin.rel_x
            py = cy + pin.rel_y

            # Alvéole carrée
            painter.setPen(QPen(QColor("#3f3f46"), 0.8))
            painter.setBrush(QBrush(QColor("#09090b")))
            painter.drawRect(QRectF(px - 2.5, py - 2.5, 5.0, 5.0))

            # Point de contact doré interne
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawRect(QRectF(px - 1.0, py - 1.0, 2.0, 2.0))

            # Libellé sérigraphié blanc
            painter.setPen(QColor("#f8fafc"))
            if pin.rel_x < 0:
                painter.drawText(QRectF(px + 6, py - 4.0, 20, 8), Qt.AlignLeft | Qt.AlignVCenter, pin.label)
            else:
                painter.drawText(QRectF(px - 26, py - 4.0, 20, 8), Qt.AlignRight | Qt.AlignVCenter, pin.label)

    def set_gpio2_led(self, state: bool):
        if self.gpio2_led_state != state:
            self.gpio2_led_state = state
            self.update()
