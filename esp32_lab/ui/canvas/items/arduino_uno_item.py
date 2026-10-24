"""
Rendu graphique ultra-réaliste de la carte Arduino Uno R3
PCB bleu Arduino signature (#00878F), connecteur USB type B chromé, jack d'alimentation noir,
puce ATmega328P DIP-28 avec encoche, résonateur à quartz 16 MHz, bouton Reset métallique,
LEDs SMD (ON verte, L D13 orange, TX/RX jaunes), barrettes femelles de broches physiques.
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

from .pin_item import PhysicalPinItem, PinAnchorItem


class ArduinoUnoGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'une carte Arduino Uno R3."""

    def __init__(self, board_id: str = "arduino_uno", parent=None):
        super().__init__(parent)
        self.board_id = board_id
        self.component_id = board_id
        self.width = 190.0   # Largeur en pixels
        self.height = 140.0  # Hauteur en pixels
        self.pin_anchors: dict[str, PinAnchorItem] = {}
        self.d13_led_state = False
        self.tx_led_state = False
        self.rx_led_state = False
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

    def set_led_state(self, pin: int | str, state: bool):
        pin_str = str(pin).upper()
        if pin_str in ("13", "D13", "GPIO13"):
            if self.d13_led_state != state:
                self.d13_led_state = bool(state)
                self.update()

    def get_usb_socket_scene_pos(self) -> QPointF:
        """Retourne la position globale du port USB-B sur le bord gauche de la carte."""
        return self.mapToScene(QPointF(2.0, 26.0))

    def _setup_pins(self):
        # 1. Rangée numérique supérieure (haut, y = 14 px)
        # Digital 0..7 (droite à gauche ou gauche à droite)
        # Disposition standard Arduino Uno R3 de gauche à droite sur le connecteur haut :
        # Connecteur haut-gauche : SCL, SDA, AREF, GND, D13, D12, D11, D10, D9, D8
        # Connecteur haut-droite : D7, D6, D5, D4, D3, D2, D1(TX), D0(RX)
        top_y = 14.0
        
        # Haut droite (D7 à D0)
        d_low_pins = [
            ("D7", "7", 7, 72.0, "Broche numérique 7"),
            ("D6", "~6", 6, 80.5, "Broche numérique 6 / PWM"),
            ("D5", "~5", 5, 89.0, "Broche numérique 5 / PWM"),
            ("D4", "4", 4, 97.5, "Broche numérique 4"),
            ("D3", "~3", 3, 106.0, "Broche numérique 3 / PWM / INT1"),
            ("D2", "2", 2, 114.5, "Broche numérique 2 / INT0"),
            ("D1", "TX", 1, 123.0, "Broche numérique 1 / TX Série"),
            ("D0", "RX", 0, 131.5, "Broche numérique 0 / RX Série"),
        ]

        # Haut gauche (D8 à D13, GND, AREF)
        d_high_pins = [
            ("D8", "8", 8, 142.0, "Broche numérique 8"),
            ("D9", "~9", 9, 150.5, "Broche numérique 9 / PWM"),
            ("D10", "~10", 10, 159.0, "Broche numérique 10 / PWM / SS"),
            ("D11", "~11", 11, 167.5, "Broche numérique 11 / PWM / MOSI"),
            ("D12", "12", 12, 176.0, "Broche numérique 12 / MISO"),
            ("D13", "13", 13, 184.5, "Broche numérique 13 / LED L / SCK"),
            ("GND_3", "GND", None, 193.0, "Masse numérique"),
            ("AREF", "AREF", None, 201.5, "Référence tension analogique"),
        ]

        # Ajustement des coordonnées X pour centrage esthétique sur la carte (width=190)
        # Décale les coordonnées pour les loger dans la largeur 190 px
        # Connecteur Haut Gauche (x de 100 à 180)
        top_defs = [
            ("D0", "RX", 0, 178.0),
            ("D1", "TX", 1, 169.5),
            ("D2", "2", 2, 161.0),
            ("D3", "~3", 3, 152.5),
            ("D4", "4", 4, 144.0),
            ("D5", "~5", 5, 135.5),
            ("D6", "~6", 6, 127.0),
            ("D7", "7", 7, 118.5),
            # Espace de 10px entre D7 et D8 (caractéristique physique de l'Uno)
            ("D8", "8", 8, 106.0),
            ("D9", "~9", 9, 97.5),
            ("D10", "~10", 10, 89.0),
            ("D11", "~11", 11, 80.5),
            ("D12", "12", 12, 72.0),
            ("D13", "13", 13, 63.5),
            ("GND_3", "GND", None, 55.0),
            ("AREF", "AREF", None, 46.5),
        ]

        for pid, lbl, gnum, px in top_defs:
            anchor = PhysicalPinItem(
                owner_id=self.board_id,
                pin_id=pid,
                pin_name=lbl,
                pin_length=12.0,
                pin_thickness=1.6,
                parent=self,
            )
            anchor.gpio_num = gnum
            anchor.role = "gpio" if gnum is not None else ("ground" if "GND" in pid else "control")
            anchor.setPos(px, top_y)
            self.pin_anchors[pid] = anchor
            if gnum is not None:
                self.pin_anchors[f"D{gnum}"] = anchor
                self.pin_anchors[f"GPIO{gnum}"] = anchor
                self.pin_anchors[str(gnum)] = anchor

        # 2. Rangée inférieure (Alimentation & Entrées Analogiques, y = 126 px)
        bot_y = 126.0
        power_defs = [
            ("IOREF", "IOREF", None, 55.0),
            ("RESET", "RESET", None, 63.5),
            ("3V3", "3.3V", None, 72.0),
            ("5V", "5V", None, 80.5),
            ("GND_1", "GND", None, 89.0),
            ("GND_2", "GND", None, 97.5),
            ("VIN", "VIN", None, 106.0),
        ]

        analog_defs = [
            ("A0", "A0", 14, 127.0),
            ("A1", "A1", 15, 135.5),
            ("A2", "A2", 16, 144.0),
            ("A3", "A3", 17, 152.5),
            ("A4", "A4", 18, 161.0),
            ("A5", "A5", 19, 169.5),
        ]

        for pid, lbl, gnum, px in power_defs:
            anchor = PhysicalPinItem(
                owner_id=self.board_id,
                pin_id=pid,
                pin_name=lbl,
                pin_length=12.0,
                pin_thickness=1.6,
                parent=self,
            )
            anchor.gpio_num = None
            anchor.role = "ground" if "GND" in pid else "power"
            anchor.setPos(px, bot_y)
            self.pin_anchors[pid] = anchor

        self.pin_anchors["GND"] = self.pin_anchors["GND_1"]
        self.pin_anchors["3.3V"] = self.pin_anchors["3V3"]

        for pid, lbl, gnum, px in analog_defs:
            anchor = PhysicalPinItem(
                owner_id=self.board_id,
                pin_id=pid,
                pin_name=lbl,
                pin_length=12.0,
                pin_thickness=1.6,
                parent=self,
            )
            anchor.gpio_num = gnum
            anchor.role = "analog"
            anchor.setPos(px, bot_y)
            self.pin_anchors[pid] = anchor
            self.pin_anchors[str(gnum)] = anchor
            self.pin_anchors[f"GPIO{gnum}"] = anchor

    def get_pin_anchor(self, pin_id: str | int) -> PinAnchorItem | None:
        """Recherche une broche physique par son identifiant ('D13', 13, 'A0', '5V', etc.)."""
        p_str = str(pin_id).strip().upper()
        if p_str in self.pin_anchors:
            return self.pin_anchors[p_str]
        if p_str.startswith("GPIO") and p_str[4:] in self.pin_anchors:
            return self.pin_anchors[p_str[4:]]
        if p_str.startswith("D") and p_str[1:] in self.pin_anchors:
            return self.pin_anchors[p_str[1:]]
        return self.pin_anchors.get(p_str)

    def boundingRect(self) -> QRectF:
        return QRectF(-10, -10, self.width + 20, self.height + 20)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée sous le PCB
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
        painter.drawRoundedRect(QRectF(4, 5, self.width, self.height), 8, 8)

        # 2. PCB Bleu Arduino signature avec chanfrein
        pcb_grad = QLinearGradient(0, 0, self.width, self.height)
        pcb_grad.setColorAt(0.0, QColor("#00878f"))  # Arduino Teal
        pcb_grad.setColorAt(0.5, QColor("#006d75"))
        pcb_grad.setColorAt(1.0, QColor("#005359"))

        painter.setPen(QPen(QColor("#00a3ad"), 1.5))
        painter.setBrush(QBrush(pcb_grad))
        
        # Forme Arduino Uno avec encoches réalistes
        pcb_path = QPainterPath()
        pcb_path.moveTo(6, 0)
        pcb_path.lineTo(self.width - 6, 0)
        pcb_path.quadTo(self.width, 0, self.width, 6)
        pcb_path.lineTo(self.width, self.height - 6)
        pcb_path.quadTo(self.width, self.height, self.width - 6, self.height)
        pcb_path.lineTo(6, self.height)
        pcb_path.quadTo(0, self.height, 0, self.height - 6)
        pcb_path.lineTo(0, 6)
        pcb_path.quadTo(0, 0, 6, 0)
        painter.drawPath(pcb_path)

        # 3. Trous de montage dorés ENIG
        self._paint_mounting_holes(painter)

        # 4. Connecteur USB Type-B chromé (haut gauche)
        self._paint_usb_b_port(painter)

        # 5. Connecteur Jack d'alimentation DC (bas gauche)
        self._paint_dc_jack(painter)

        # 6. Puce ATmega328P DIP-28 (au centre droit)
        self._paint_atmega328p_dip(painter)

        # 7. Quartz 16 MHz et puce USB ATmega16U2
        self._paint_usb_chip_and_crystal(painter)

        # 8. Bouton Reset métallique (haut gauche)
        self._paint_reset_button(painter)

        # 9. LEDs CMS (ON, L, TX, RX)
        self._paint_leds(painter)

        # 10. Barrettes de connecteurs femelles noires et sérigraphie blanche
        self._paint_headers_and_silkscreen(painter)

    def _paint_mounting_holes(self, painter: QPainter):
        hole_coords = [(14, 48), (14, 116), (self.width - 14, 28), (self.width - 14, 108)]
        for hx, hy in hole_coords:
            painter.setPen(QPen(QColor("#d97706"), 1))
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawEllipse(QPointF(hx, hy), 4.0, 4.0)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawEllipse(QPointF(hx, hy), 2.2, 2.2)

    def _paint_usb_b_port(self, painter: QPainter):
        """Connecteur USB Type B métallique robuste (déborde légèrement à gauche)."""
        usb_rect = QRectF(-4, 14, 30, 24)
        usb_grad = QLinearGradient(-4, 14, 26, 38)
        usb_grad.setColorAt(0.0, QColor("#e2e8f0"))
        usb_grad.setColorAt(0.4, QColor("#cbd5e1"))
        usb_grad.setColorAt(0.8, QColor("#94a3b8"))
        usb_grad.setColorAt(1.0, QColor("#64748b"))

        painter.setPen(QPen(QColor("#475569"), 1.0))
        painter.setBrush(QBrush(usb_grad))
        painter.drawRoundedRect(usb_rect, 2, 2)

        # Cavité interne USB-B biseautée
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRoundedRect(QRectF(-2, 18, 12, 16), 1.5, 1.5)

    def _paint_dc_jack(self, painter: QPainter):
        """Prise jack d'alimentation DC 2.1mm cylindrique noire."""
        jack_rect = QRectF(-4, 98, 28, 26)
        jack_grad = QLinearGradient(-4, 98, 24, 124)
        jack_grad.setColorAt(0.0, QColor("#1e293b"))
        jack_grad.setColorAt(0.5, QColor("#0f172a"))
        jack_grad.setColorAt(1.0, QColor("#020617"))

        painter.setPen(QPen(QColor("#334155"), 1.0))
        painter.setBrush(QBrush(jack_grad))
        painter.drawRoundedRect(jack_rect, 2, 2)

        # Trou central et broche métallique interne
        painter.setBrush(QBrush(QColor("#000000")))
        painter.drawEllipse(QPointF(10, 111), 6, 6)
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawEllipse(QPointF(10, 111), 2, 2)

    def _paint_atmega328p_dip(self, painter: QPainter):
        """Microcontrôleur ATmega328P en boîtier DIP-28 avec support tulipe."""
        # Support tulipe noir externe
        socket_rect = QRectF(78, 62, 70, 24)
        painter.setPen(QPen(QColor("#09090b"), 1.0))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(socket_rect, 2, 2)

        # Corps plastique noir de la puce IC
        chip_rect = QRectF(80, 64, 66, 20)
        chip_grad = QLinearGradient(80, 64, 146, 84)
        chip_grad.setColorAt(0.0, QColor("#27272a"))
        chip_grad.setColorAt(0.5, QColor("#18181b"))
        chip_grad.setColorAt(1.0, QColor("#09090b"))

        painter.setPen(QPen(QColor("#3f3f46"), 0.8))
        painter.setBrush(QBrush(chip_grad))
        painter.drawRoundedRect(chip_rect, 1.5, 1.5)

        # Encoche demi-lune de repère à gauche
        painter.setPen(QPen(QColor("#3f3f46"), 0.8))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawChord(QRectF(78, 71, 6, 6), 90 * 16, -180 * 16)

        # 14 pattes argentées en haut et 14 en bas
        painter.setPen(QPen(QColor("#cbd5e1"), 1.2))
        for i in range(14):
            leg_x = 83 + i * 4.6
            painter.drawLine(QPointF(leg_x, 62), QPointF(leg_x, 64))
            painter.drawLine(QPointF(leg_x, 84), QPointF(leg_x, 86))

        # Sérigraphie laser de la puce
        font_chip = QFont("Arial", 4, QFont.Bold)
        painter.setFont(font_chip)
        painter.setPen(QColor("#a1a1aa"))
        painter.drawText(QRectF(84, 66, 60, 8), Qt.AlignCenter, "ATMEGA328P-PU")
        painter.setFont(QFont("Arial", 3, QFont.Normal))
        painter.drawText(QRectF(84, 74, 60, 7), Qt.AlignCenter, "ATMEL")

    def _paint_usb_chip_and_crystal(self, painter: QPainter):
        """Puce convertisseur USB ATmega16U2 QFN et quartz oscillateur 16MHz."""
        # ATmega16U2
        qfn_rect = QRectF(38, 48, 14, 14)
        painter.setPen(QPen(QColor("#3f3f46"), 0.6))
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(qfn_rect, 1, 1)

        # Quartz 16 MHz boîtier ovale métallique argenté
        xtal_rect = QRectF(56, 49, 14, 7)
        xtal_grad = QLinearGradient(56, 49, 70, 56)
        xtal_grad.setColorAt(0.0, QColor("#e2e8f0"))
        xtal_grad.setColorAt(0.5, QColor("#94a3b8"))
        xtal_grad.setColorAt(1.0, QColor("#cbd5e1"))

        painter.setPen(QPen(QColor("#64748b"), 0.6))
        painter.setBrush(QBrush(xtal_grad))
        painter.drawRoundedRect(xtal_rect, 3, 3)

    def _paint_reset_button(self, painter: QPainter):
        """Bouton poussoir Reset à bouton rouge ou métallique."""
        btn_rect = QRectF(14, 8, 10, 10)
        painter.setPen(QPen(QColor("#64748b"), 0.8))
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawRoundedRect(btn_rect, 1.5, 1.5)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#dc2626")))  # Poussoir rouge
        painter.drawEllipse(QPointF(19, 13), 2.8, 2.8)

        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(QRectF(10, 18, 18, 6), Qt.AlignCenter, "RESET")

    def _paint_leds(self, painter: QPainter):
        """LEDs SMD intégrées : ON (verte), L sur D13 (orange), TX/RX (jaunes)."""
        # 1. LED ON (verte, s'allume si la carte est alimentée)
        on_pos = QPointF(42, 70)
        if self.is_powered:
            painter.setPen(QPen(QColor("#065f46"), 0.5))
            painter.setBrush(QBrush(QColor("#10b981")))
            painter.drawRect(QRectF(on_pos.x() - 1.5, on_pos.y() - 2.5, 3, 5))

            glow = QRadialGradient(on_pos, 7)
            glow.setColorAt(0.0, QColor(16, 185, 129, 200))
            glow.setColorAt(1.0, QColor(16, 185, 129, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(on_pos, 6, 6)
        else:
            painter.setPen(QPen(QColor("#022c22"), 0.5))
            painter.setBrush(QBrush(QColor("#064e3b")))
            painter.drawRect(QRectF(on_pos.x() - 1.5, on_pos.y() - 2.5, 3, 5))

        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(QRectF(on_pos.x() - 6, on_pos.y() + 3.5, 12, 5), Qt.AlignCenter, "ON")

        # 2. LED L (orange/jaune, reliée à la broche D13)
        l_pos = QPointF(52, 70)
        if self.d13_led_state and self.is_powered:
            painter.setPen(QPen(QColor("#92400e"), 0.5))
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawRect(QRectF(l_pos.x() - 1.5, l_pos.y() - 2.5, 3, 5))

            glow_l = QRadialGradient(l_pos, 8)
            glow_l.setColorAt(0.0, QColor(245, 158, 11, 220))
            glow_l.setColorAt(0.5, QColor(217, 119, 6, 100))
            glow_l.setColorAt(1.0, QColor(217, 119, 6, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow_l))
            painter.drawEllipse(l_pos, 7, 7)
        else:
            painter.setPen(QPen(QColor("#451a03"), 0.5))
            painter.setBrush(QBrush(QColor("#78350f")))
            painter.drawRect(QRectF(l_pos.x() - 1.5, l_pos.y() - 2.5, 3, 5))

        painter.setFont(QFont("Arial", 3, QFont.Bold))
        painter.setPen(QColor("#f8fafc"))
        painter.drawText(QRectF(l_pos.x() - 5, l_pos.y() + 3.5, 10, 5), Qt.AlignCenter, "L")

        # 3. LEDs TX et RX
        for x_offset, lbl, state in [(42, "TX", self.tx_led_state), (52, "RX", self.rx_led_state)]:
            y_pos = 82
            painter.setPen(QPen(QColor("#78350f"), 0.5))
            painter.setBrush(QBrush(QColor("#f59e0b" if state else "#451a03")))
            painter.drawRect(QRectF(x_offset - 1.5, y_pos - 2, 3, 4))
            painter.setPen(QColor("#cbd5e1"))
            painter.drawText(QRectF(x_offset - 5, y_pos + 2.5, 10, 5), Qt.AlignCenter, lbl)

    def _paint_headers_and_silkscreen(self, painter: QPainter):
        """Barrettes femelles en plastique noir et sérigraphie blanche nette."""
        # 1. Logo et marquage officiel Arduino Uno
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRectF(74, 34, 100, 14), Qt.AlignLeft, "ARDUINO")
        painter.setFont(QFont("Arial", 6, QFont.Bold))
        painter.setPen(QColor("#e2e8f0"))
        painter.drawText(QRectF(74, 46, 100, 12), Qt.AlignLeft, "UNO R3")

        # Carte de l'Italie stylisée en filigrane blanc
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
        path_map = QPainterPath()
        path_map.moveTo(156, 70)
        path_map.lineTo(168, 88)
        path_map.lineTo(162, 94)
        path_map.lineTo(152, 82)
        painter.drawPath(path_map)

        # Titres des sections de broches (Sérigraphie réaliste Arduino)
        font_sec = QFont("Arial", 3.2, QFont.Bold)
        painter.setFont(font_sec)
        painter.setPen(QColor("#cbd5e1"))
        painter.drawText(QRectF(42, 2, 69, 6), Qt.AlignCenter, "DIGITAL (PWM ~)")
        painter.drawText(QRectF(114, 2, 69, 6), Qt.AlignCenter, "COMMUNICATION")
        painter.drawText(QRectF(50, 132, 61, 6), Qt.AlignCenter, "POWER")
        painter.drawText(QRectF(122, 132, 53, 6), Qt.AlignCenter, "ANALOG IN")

        # Corps plastique noir des barrettes femelles
        # Barrettes supérieures (y = 14)
        painter.setPen(QPen(QColor("#27272a"), 0.8))
        painter.setBrush(QBrush(QColor("#18181b")))
        # Haut gauche (D8 à AREF) : 8 pins (46.5 à 106.0)
        painter.drawRoundedRect(QRectF(42, 9, 69, 10), 1.5, 1.5)
        # Haut droite (D7 à D0) : 8 pins (118.5 à 178.0)
        painter.drawRoundedRect(QRectF(114, 9, 69, 10), 1.5, 1.5)

        # Barrettes inférieures (y = 126)
        # Bas gauche (Power : IOREF à VIN) : 7 pins (55.0 à 106.0)
        painter.drawRoundedRect(QRectF(50, 121, 61, 10), 1.5, 1.5)
        # Bas droite (Analog In : A0 à A5) : 6 pins (127.0 à 169.5)
        painter.drawRoundedRect(QRectF(122, 121, 53, 10), 1.5, 1.5)

        # Dessin des alvéoles carrées des broches et sérigraphie blanche verticale nette
        font_pin = QFont("Arial", 3.8, QFont.Bold)
        painter.setFont(font_pin)

        unique_anchors = []
        seen = set()
        for anchor in self.pin_anchors.values():
            if id(anchor) not in seen:
                seen.add(id(anchor))
                unique_anchors.append(anchor)

        for anchor in unique_anchors:
            pos = anchor.pos()
            px, py = pos.x(), pos.y()

            # Alvéole carrée femelle
            painter.setPen(QPen(QColor("#3f3f46"), 0.8))
            painter.setBrush(QBrush(QColor("#09090b")))
            painter.drawRect(QRectF(px - 2.5, py - 2.5, 5.0, 5.0))

            # Point de contact doré interne
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.drawRect(QRectF(px - 1.0, py - 1.0, 2.0, 2.0))

            # Libellé sérigraphié blanc orienté verticalement pour éviter tout chevauchement
            painter.setPen(QColor("#ffffff"))
            lbl = anchor.pin_name

            painter.save()
            if py < 50:  # Rangée du haut (Digital pins) : s'étend verticalement sous la barrette
                painter.translate(px, py + 7.5)
                painter.rotate(90)
                painter.drawText(QRectF(0, -3.5, 16, 7), Qt.AlignLeft | Qt.AlignVCenter, lbl)
            else:  # Rangée du bas (Power / Analog) : s'étend verticalement au-dessus de la barrette
                painter.translate(px, py - 7.5)
                painter.rotate(-90)
                painter.drawText(QRectF(0, -3.5, 20, 7), Qt.AlignLeft | Qt.AlignVCenter, lbl)
            painter.restore()
