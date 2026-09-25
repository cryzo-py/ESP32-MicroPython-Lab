"""
Scène graphique schématique (SchematicScene)
Représentation électronique normalisée (normes CEI 60617 / IEEE) du circuit avec routage orthogonal netlist.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsScene

from ...app.event_bus import get_event_bus
from ...core.models.project import ProjectModel
from .items.pin_item import PinAnchorItem


class SchematicSymbolItem(QGraphicsObject):
    """Symbole électronique normalisé pour la vue schématique."""

    def __init__(self, component_id: str, comp_type: str, ref_des: str, title: str, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.comp_type = comp_type
        self.ref_des = ref_des
        self.title = title
        self.pin_positions: dict[str, QPointF] = {}
        self._init_pins()

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(2)

    def _init_pins(self):
        ctype = self.comp_type.lower()
        if ctype == "resistor":
            self.pin_positions = {"pin1": QPointF(-35, 0), "pin2": QPointF(35, 0)}
        elif ctype == "led":
            self.pin_positions = {"anode": QPointF(-25, 0), "cathode": QPointF(25, 0)}
        elif ctype == "button":
            self.pin_positions = {"pin1": QPointF(-25, 0), "pin2": QPointF(25, 0), "pin3": QPointF(-25, 10), "pin4": QPointF(25, 10)}
        elif ctype == "potentiometer":
            self.pin_positions = {"vcc": QPointF(-25, -15), "gnd": QPointF(25, -15), "sig": QPointF(0, 20)}
        elif ctype == "relay":
            self.pin_positions = {"vcc": QPointF(-40, -15), "gnd": QPointF(-40, 15), "in": QPointF(-40, 0), "com": QPointF(40, -15), "no": QPointF(40, 0), "nc": QPointF(40, 15)}
        elif ctype == "buzzer":
            self.pin_positions = {"pos": QPointF(15, -6), "neg": QPointF(15, 6), "pin1": QPointF(15, -6), "pin2": QPointF(15, 6)}
        elif ctype in ("neopixel", "ws2812", "ws2812b"):
            self.pin_positions = {"vcc": QPointF(-35, -10), "gnd": QPointF(-35, 10), "din": QPointF(-35, 0), "dout": QPointF(35, 0)}
        elif ctype == "rgb_led":
            self.pin_positions = {"r": QPointF(-25, -15), "g": QPointF(-25, -5), "b": QPointF(-25, 5), "gnd": QPointF(-25, 15)}
        elif ctype == "tm1637":
            self.pin_positions = {"vcc": QPointF(-40, -10), "gnd": QPointF(-40, 10), "dio": QPointF(40, -10), "clk": QPointF(40, 10)}
        elif ctype == "ldr":
            self.pin_positions = {"pin1": QPointF(-30, 0), "pin2": QPointF(30, 0)}
        elif ctype == "pir":
            self.pin_positions = {"vcc": QPointF(-30, -15), "out": QPointF(0, 20), "gnd": QPointF(30, -15)}
        elif ctype == "w25qxx":
            self.pin_positions = {"vcc": QPointF(-45, -20), "gnd": QPointF(-45, 20), "cs": QPointF(-45, -10), "clk": QPointF(-45, 0), "do": QPointF(45, -10), "di": QPointF(45, 0)}
        else:
            self.pin_positions = {"vcc": QPointF(-45, 12), "gnd": QPointF(-45, 22), "sda": QPointF(45, 12), "scl": QPointF(45, 22), "trig": QPointF(45, 12), "echo": QPointF(45, 22), "data": QPointF(45, 12)}

    def get_pin_scene_pos(self, pin_id: str) -> QPointF:
        key = pin_id.lower().strip()
        local_pos = self.pin_positions.get(key)
        if local_pos is None:
            for k, p in self.pin_positions.items():
                if key in k or k in key:
                    local_pos = p
                    break
        if local_pos is None:
            local_pos = QPointF(0, 0)
        return self.mapToScene(local_pos)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.scene() and hasattr(self.scene(), "update_wires"):
                self.scene().update_wires()
        return super().itemChange(change, value)

    def boundingRect(self) -> QRectF:
        return QRectF(-50, -40, 100, 80)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # Tracé selon le type normalisé
        if self.comp_type == "resistor":
            self._paint_resistor(painter)
        elif self.comp_type == "led":
            self._paint_led(painter)
        elif self.comp_type == "button":
            self._paint_button(painter)
        elif self.comp_type == "potentiometer":
            self._paint_potentiometer(painter)
        elif self.comp_type == "relay":
            self._paint_relay(painter)
        elif self.comp_type in ("neopixel", "ws2812"):
            self._paint_neopixel(painter)
        elif self.comp_type == "buzzer":
            self._paint_buzzer(painter)
        else:
            self._paint_ic_block(painter)

    def _paint_resistor(self, painter: QPainter):
        pen = QPen(QColor("#38bdf8"), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        # Boîtier rectangulaire normalisé CEI
        rect = QRectF(-25, -10, 50, 20)
        painter.drawRect(rect)
        # Bornes axiales
        painter.drawLine(-35, 0, -25, 0)
        painter.drawLine(25, 0, 35, 0)
        self.pin_positions["pin1"] = QPointF(-35, 0)
        self.pin_positions["pin2"] = QPointF(35, 0)
        # Label
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(-35, -28, 70, 16), Qt.AlignCenter, self.ref_des)

    def _paint_led(self, painter: QPainter):
        pen = QPen(QColor("#ef4444"), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#ef4444" if getattr(self, "is_on", False) else "#0f172a")))
        # Diode triangle
        path = QPainterPath()
        path.moveTo(-12, -14)
        path.lineTo(-12, 14)
        path.lineTo(12, 0)
        path.closeSubpath()
        painter.drawPath(path)
        # Barre cathode
        painter.drawLine(12, -14, 12, 14)
        # Flèches d'émission lumineuse
        painter.drawLine(4, -16, 12, -24)
        painter.drawLine(10, -14, 18, -22)
        # Bornes
        painter.setPen(QPen(QColor("#cbd5e1"), 2))
        painter.drawLine(-25, 0, -12, 0)
        painter.drawLine(12, 0, 25, 0)
        self.pin_positions["anode"] = QPointF(-25, 0)
        self.pin_positions["cathode"] = QPointF(25, 0)
        # Label
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(-30, -32, 60, 16), Qt.AlignCenter, self.ref_des)

    def _paint_button(self, painter: QPainter):
        pen = QPen(QColor("#38bdf8"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        # Bornes avec pastilles rondes
        painter.drawEllipse(QPointF(-16, 0), 3, 3)
        painter.drawEllipse(QPointF(16, 0), 3, 3)
        # Ligne de contact ouverte
        painter.drawLine(-16, -2, 14, -14)
        # Tringle de commande
        painter.drawLine(0, -8, 0, -18)
        painter.drawLine(-8, -18, 8, -18)
        # Sorties
        painter.drawLine(-30, 0, -16, 0)
        painter.drawLine(16, 0, 30, 0)
        self.pin_positions["1a"] = QPointF(-30, 0)
        self.pin_positions["2a"] = QPointF(30, 0)
        self.pin_positions["1b"] = QPointF(-30, 0)
        self.pin_positions["2b"] = QPointF(30, 0)
        # Label
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(-30, -32, 60, 16), Qt.AlignCenter, self.ref_des)

    def _paint_potentiometer(self, painter: QPainter):
        pen = QPen(QColor("#fbbf24"), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRect(QRectF(-20, -10, 40, 20))
        # Curseur flèche au centre
        arrow = QPainterPath()
        arrow.moveTo(0, 25)
        arrow.lineTo(0, 12)
        arrow.lineTo(-4, 16)
        arrow.moveTo(0, 12)
        arrow.lineTo(4, 16)
        painter.drawPath(arrow)
        # Bornes
        painter.drawLine(-30, 0, -20, 0)
        painter.drawLine(20, 0, 30, 0)
        self.pin_positions["vcc"] = QPointF(-30, 0)
        self.pin_positions["gnd"] = QPointF(30, 0)
        self.pin_positions["sig"] = QPointF(0, 25)
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(-30, -26, 60, 16), Qt.AlignCenter, self.ref_des)

    def _paint_relay(self, painter: QPainter):
        pen = QPen(QColor("#3b82f6"), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRoundedRect(QRectF(-35, -25, 70, 50), 3, 3)
        # Bobine à droite (IN/GND)
        painter.drawText(QRectF(10, -20, 20, 15), Qt.AlignCenter, "IN")
        painter.drawText(QRectF(10, 5, 20, 15), Qt.AlignCenter, "GND")
        # Contacts à gauche (NO, COM, NC)
        painter.drawText(QRectF(-30, -20, 25, 12), Qt.AlignCenter, "NO")
        painter.drawText(QRectF(-30, -6, 25, 12), Qt.AlignCenter, "COM")
        painter.drawText(QRectF(-30, 8, 25, 12), Qt.AlignCenter, "NC")
        self.pin_positions["no"] = QPointF(-35, -14)
        self.pin_positions["com"] = QPointF(-35, 0)
        self.pin_positions["nc"] = QPointF(-35, 14)
        self.pin_positions["vcc"] = QPointF(35, -14)
        self.pin_positions["in"] = QPointF(35, 0)
        self.pin_positions["gnd"] = QPointF(35, 14)
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(-35, -40, 70, 16), Qt.AlignCenter, self.ref_des)

    def _paint_neopixel(self, painter: QPainter):
        pen = QPen(QColor("#10b981"), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRoundedRect(QRectF(-30, -20, 60, 40), 4, 4)
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Consolas", 7, QFont.Bold))
        painter.drawText(QRectF(-28, -8, 56, 16), Qt.AlignCenter, "WS2812B")
        self.pin_positions["5v"] = QPointF(-20, 20)
        self.pin_positions["din"] = QPointF(-7, 20)
        self.pin_positions["dout"] = QPointF(7, 20)
        self.pin_positions["gnd"] = QPointF(20, 20)
        painter.drawText(QRectF(-30, -34, 60, 16), Qt.AlignCenter, self.ref_des)

    def _paint_buzzer(self, painter: QPainter):
        pen = QPen(QColor("#fbbf24"), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawChord(QRectF(-15, -15, 30, 30), -90 * 16, 180 * 16)
        painter.drawLine(0, -15, -15, -25)
        painter.drawLine(0, 15, -15, 25)
        self.pin_positions["pos"] = QPointF(15, -6)
        self.pin_positions["neg"] = QPointF(15, 6)
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(-30, -32, 60, 16), Qt.AlignCenter, self.ref_des)

    def _paint_ic_block(self, painter: QPainter):
        """Bloc de circuit intégré générique (OLED, LCD, DHT22, HC-SR04)."""
        pen = QPen(QColor("#38bdf8"), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.drawRoundedRect(QRectF(-45, -30, 90, 60), 4, 4)
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(-45, -26, 90, 16), Qt.AlignCenter, self.ref_des)
        painter.setFont(QFont("Segoe UI", 7))
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(QRectF(-45, -8, 90, 16), Qt.AlignCenter, self.title)

        # Configurer broches usuelles
        self.pin_positions["vcc"] = QPointF(-45, 12)
        self.pin_positions["gnd"] = QPointF(-45, 22)
        self.pin_positions["sda"] = QPointF(45, 12)
        self.pin_positions["scl"] = QPointF(45, 22)
        self.pin_positions["trig"] = QPointF(45, 12)
        self.pin_positions["echo"] = QPointF(45, 22)
        self.pin_positions["data"] = QPointF(45, 12)


class ESP32SchematicItem(QGraphicsObject):
    """Symbole normalisé pour le microcontrôleur ESP32 DevKit."""

    def __init__(self, component_id: str = "esp32", parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(2)
        self.pin_positions: dict[str, QPointF] = {}
        self._init_pin_positions()

    def _init_pin_positions(self):
        # Broches à gauche (Alim & Analogique)
        left_pins = ["3V3", "EN", "GPIO36", "GPIO39", "GPIO34", "GPIO35", "GPIO32", "GPIO33", "GPIO25", "GPIO26", "GPIO27", "GPIO14", "GPIO12", "GND_1"]
        for i, pin in enumerate(left_pins):
            y = -130 + i * 20
            self.pin_positions[pin.lower()] = QPointF(-70, y)

        # Broches à droite (Bus numériques & PWM)
        right_pins = ["5V", "GPIO23", "GPIO22", "GPIO1", "GPIO3", "GPIO21", "GPIO19", "GPIO18", "GPIO5", "GPIO17", "GPIO16", "GPIO4", "GPIO2", "GPIO15", "GND_2"]
        for i, pin in enumerate(right_pins):
            y = -130 + i * 20
            self.pin_positions[pin.lower()] = QPointF(70, y)

    def get_pin_scene_pos(self, pin_id: str) -> QPointF:
        key = pin_id.lower()
        if key.startswith("gnd"):
            key = "gnd_1" if "1" in key else "gnd_2" if "2" in key else "gnd_1"
        pos = self.pin_positions.get(key, QPointF(-70, 0))
        return self.mapToScene(pos)

    def boundingRect(self) -> QRectF:
        return QRectF(-85, -160, 170, 320)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        # Corps principal CI
        painter.setPen(QPen(QColor("#38bdf8"), 2))
        painter.setBrush(QBrush(QColor("#0a1128")))
        painter.drawRoundedRect(QRectF(-60, -145, 120, 290), 4, 4)

        # Encoche d'orientation IC en haut
        painter.drawArc(QRectF(-12, -152, 24, 14), 0, -180 * 16)

        # Titre
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.setPen(QColor("#38bdf8"))
        painter.drawText(QRectF(-60, -140, 120, 20), Qt.AlignCenter, "U1: ESP32")
        painter.setFont(QFont("Segoe UI", 7))
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(QRectF(-60, -122, 120, 16), Qt.AlignCenter, "WROOM-32")

        # Dessin des broches
        painter.setFont(QFont("Consolas", 7))
        for pin_name, pos in self.pin_positions.items():
            is_left = pos.x() < 0
            # Ligne de broche
            painter.setPen(QPen(QColor("#475569"), 1.5))
            if is_left:
                painter.drawLine(pos.x(), pos.y(), pos.x() + 10, pos.y())
                painter.setPen(QColor("#e2e8f0"))
                painter.drawText(QRectF(pos.x() + 12, pos.y() - 8, 44, 16), Qt.AlignLeft | Qt.AlignVCenter, pin_name.upper())
            else:
                painter.drawLine(pos.x() - 10, pos.y(), pos.x(), pos.y())
                painter.setPen(QColor("#e2e8f0"))
                painter.drawText(QRectF(pos.x() - 56, pos.y() - 8, 44, 16), Qt.AlignRight | Qt.AlignVCenter, pin_name.upper())


class SchematicWireItem(QGraphicsObject):
    """Fil de raccordement schématique orthogonal (angles droits avec points de dérivation)."""

    def __init__(self, p1: QPointF, p2: QPointF, color: str = "#38bdf8", parent=None):
        super().__init__(parent)
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.setZValue(1)

    def set_endpoints(self, p1: QPointF, p2: QPointF):
        self.prepareGeometryChange()
        self.p1 = p1
        self.p2 = p2
        self.update()

    def boundingRect(self) -> QRectF:
        x_min = min(self.p1.x(), self.p2.x()) - 10
        x_max = max(self.p1.x(), self.p2.x()) + 10
        y_min = min(self.p1.y(), self.p2.y()) - 10
        y_max = max(self.p1.y(), self.p2.y()) + 10
        return QRectF(x_min, y_min, x_max - x_min, y_max - y_min)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.color), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)

        # Routage orthogonal type Manhattan : (x1, y1) -> (mid_x, y1) -> (mid_x, y2) -> (x2, y2)
        mid_x = (self.p1.x() + self.p2.x()) / 2.0
        path = QPainterPath()
        path.moveTo(self.p1)
        path.lineTo(mid_x, self.p1.y())
        path.lineTo(mid_x, self.p2.y())
        path.lineTo(self.p2)
        painter.drawPath(path)

        # Points de dérivation ronds aux extrémités
        painter.setBrush(QBrush(QColor(self.color)))
        painter.drawEllipse(self.p1, 2.5, 2.5)
        painter.drawEllipse(self.p2, 2.5, 2.5)


class SchematicScene(QGraphicsScene):
    """Scène affichant le schéma électrique complet d'un projet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_name = "dark"
        self.setBackgroundBrush(QColor("#070d1e")) # Bleu nuit technique style KiCad/EDA
        self.symbols: dict[str, QGraphicsItem] = {}
        self.wires: list[tuple[SchematicWireItem, str, str, str, str]] = []

    def set_theme(self, theme_name: str = "dark"):
        """Ajuste le fond et la grille du schéma selon le thème."""
        self.theme_name = theme_name
        if theme_name == "light":
            self.setBackgroundBrush(QColor("#ffffff"))
        else:
            self.setBackgroundBrush(QColor("#070d1e"))
        self.update()

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        # Quadrillage de repérage millimétré
        grid_col = QColor("#f1f5f9") if getattr(self, "theme_name", "dark") == "light" else QColor("#132247")
        painter.setPen(QPen(grid_col, 1))
        step = 20
        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)

        for x in range(left, int(rect.right()), step):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()), step):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    def load_project_schematic(self, project: ProjectModel):
        """Construit le schéma électronique à partir du modèle de projet."""
        self.clear()
        self.symbols.clear()
        self.wires.clear()

        # 1. Symbole ESP32 central
        esp32_item = ESP32SchematicItem()
        esp32_item.setPos(50, 80)
        self.addItem(esp32_item)
        self.symbols["esp32"] = esp32_item

        # 2. Placement des symboles des composants
        type_counters: dict[str, int] = {}
        comp_x = 320
        comp_y = -80

        for comp in project.components:
            if comp.type == "breadboard":
                continue # La platine d'essai n'a pas de symbole propre en schéma de principe

            ctype = comp.type.lower()
            type_counters[ctype] = type_counters.get(ctype, 0) + 1
            idx = type_counters[ctype]

            ref_prefix = {
                "resistor": "R", "led": "D", "button": "SW", "potentiometer": "RV",
                "relay": "K", "neopixel": "U_LED", "buzzer": "BZ", "servo": "M",
                "dht22": "SEN", "oled": "DISP", "lcd": "DISP", "hcsr04": "U"
            }.get(ctype, "U")

            ref_des = f"{ref_prefix}{idx}"
            sym = SchematicSymbolItem(comp.id, ctype, ref_des, comp.name or ctype.upper())
            sym.setPos(comp_x, comp_y)
            self.addItem(sym)
            self.symbols[comp.id] = sym

            # Décalage en grille pour les composants suivants
            comp_y += 100
            if comp_y > 280:
                comp_y = -80
                comp_x += 160

        # 3. Tracé des liaisons équipotentielles (résolution automatique des nœuds breadboard)
        graph: dict[tuple[str, str], set[tuple[str, str]]] = {}
        def add_g_edge(u, v):
            u_norm = (str(u[0]).lower(), str(u[1]).lower())
            v_norm = (str(v[0]).lower(), str(v[1]).lower())
            graph.setdefault(u_norm, set()).add(v_norm)
            graph.setdefault(v_norm, set()).add(u_norm)

        for conn in project.connections:
            p1 = (conn.from_component, conn.from_pin)
            p2 = (conn.to_component, conn.to_pin)
            add_g_edge(p1, p2)

        # Si breadboard présente, lier les composants insérés et les trous d'une même rangée/rail
        bb_comp = next((c for c in project.components if c.type == "breadboard"), None)

        # Connecter les composants insérés dans la breadboard (pin_insertions)
        if bb_comp:
            for comp in project.components:
                if comp.type == "breadboard":
                    continue
                for pin_id, hole_id in getattr(comp, "pin_insertions", {}).items():
                    add_g_edge((comp.id, pin_id), (bb_comp.id, hole_id))

        if bb_comp:
            bb_id = bb_comp.id.lower()
            bb_pins = [p for p in graph.keys() if p[0] == bb_id]
            from collections import defaultdict
            strip_map = defaultdict(list)
            for _, pid in bb_pins:
                p_lower = pid.lower()
                if p_lower.startswith("r") and "_" in p_lower:
                    parts = p_lower.split("_")
                    row = parts[0]
                    col = parts[1] if len(parts) > 1 else "a"
                    half = "left" if col in "abcde" else "right"
                    strip_map[f"{row}_{half}"].append(pid)
                elif "minus" in p_lower:
                    strip_map["gnd_rail"].append(pid)
                elif "plus" in p_lower:
                    strip_map["vcc_rail"].append(pid)
            for strip, pids in strip_map.items():
                if len(pids) >= 2:
                    first = (bb_id, pids[0])
                    for other in pids[1:]:
                        add_g_edge(first, (bb_id, other))

        # Relier les symboles schématiques connectés
        drawn_pairs = set()
        # Symboles et leurs broches normalisées
        symbol_map = {k.lower(): s for k, s in self.symbols.items()}
        symbol_pins = []
        for c_id_lower, s in symbol_map.items():
            for p_name in getattr(s, "pin_positions", {}).keys():
                symbol_pins.append((c_id_lower, p_name.lower()))

        for sp in symbol_pins:
            visited = set()
            queue = [sp]
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    for nxt in graph.get(curr, set()):
                        if nxt not in visited:
                            queue.append(nxt)
            for reach in visited:
                if reach != sp and reach in symbol_pins:
                    pair = tuple(sorted([sp, reach]))
                    if pair not in drawn_pairs:
                        drawn_pairs.add(pair)
                        s1 = symbol_map.get(sp[0])
                        s2 = symbol_map.get(reach[0])
                        if s1 and s2:
                            p1 = s1.get_pin_scene_pos(sp[1])
                            p2 = s2.get_pin_scene_pos(reach[1])
                            wire = SchematicWireItem(p1, p2, "#38bdf8")
                            self.addItem(wire)
                            self.wires.append((wire, sp[0], sp[1], reach[0], reach[1]))

    def update_wires(self):
        for wire, from_c, from_p, to_c, to_p in self.wires:
            s_from = self.symbols.get(from_c)
            s_to = self.symbols.get(to_c)
            if s_from and s_to:
                p1 = s_from.get_pin_scene_pos(from_p)
                p2 = s_to.get_pin_scene_pos(to_p)
                wire.set_endpoints(p1, p2)