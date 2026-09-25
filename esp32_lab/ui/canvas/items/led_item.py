"""
Rendu graphique ultra-réaliste d'une diode électroluminescente (LED 5mm traversante)
Dôme époxy translucide avec collerette et méplat (cathode), électrodes internes visibles
(enclume et tige), pattes métalliques en cuivre étamé, et diffusion lumineuse volumétrique.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PinAnchorItem, PhysicalPinItem


class LEDGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'une LED standard 5 mm avec ses pattes réelles."""

    COLOR_MAP = {
        "red": {"main": "#ef4444", "glow": "#f87171", "dark": "#7f1d1d", "tint": (239, 68, 68)},
        "green": {"main": "#22c55e", "glow": "#4ade80", "dark": "#14532d", "tint": (34, 197, 94)},
        "blue": {"main": "#3b82f6", "glow": "#60a5fa", "dark": "#1e3a8a", "tint": (59, 130, 246)},
        "yellow": {"main": "#eab308", "glow": "#fde047", "dark": "#713f12", "tint": (234, 179, 8)},
        "white": {"main": "#f8fafc", "glow": "#ffffff", "dark": "#94a3b8", "tint": (248, 250, 252)},
    }

    @classmethod
    def normalize_color_name(cls, color_name: str) -> str:
        s = str(color_name).lower().strip()
        if s in cls.COLOR_MAP:
            return s
        aliases = {
            "vert": "green", "verte": "green", "#22c55e": "green", "#10b981": "green", "#16a34a": "green", "#4ade80": "green",
            "rouge": "red", "#ef4444": "red", "#dc2626": "red", "#f87171": "red", "#b91c1c": "red",
            "bleu": "blue", "bleue": "blue", "#3b82f6": "blue", "#38bdf8": "blue", "#0ea5e9": "blue", "#2563eb": "blue", "#60a5fa": "blue",
            "jaune": "yellow", "#eab308": "yellow", "#facc15": "yellow", "#ca8a04": "yellow",
            "blanc": "white", "blanche": "white", "#ffffff": "white", "#f8fafc": "white",
        }
        if s in aliases:
            return aliases[s]
        qc = QColor(s)
        if qc.isValid():
            h, s_val, v, _ = qc.getHsv()
            if s_val < 30:
                return "white"
            if 35 <= h < 75:
                return "yellow"
            elif 75 <= h < 170:
                return "green"
            elif 170 <= h < 260:
                return "blue"
            else:
                return "red"
        return "red"

    def __init__(self, component_id: str, color_name: str = "red", parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.color_name = self.normalize_color_name(color_name)
        self.is_on = False
        self.brightness = 0.0

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # Deux broches métalliques traversantes physiques (cuivre étamé)
        # Anode (+) à y = 25.5, Cathode (-) à y = 34.0
        self.anode_pin = PhysicalPinItem(component_id, "anode", "+ (Anode)", pin_length=24.0, pin_thickness=1.8, parent=self)
        self.anode_pin.setPos(0, 25.5)

        self.cathode_pin = PhysicalPinItem(component_id, "cathode", "- (Cathode)", pin_length=28.0, pin_thickness=1.8, parent=self)
        self.cathode_pin.setPos(0, 34.0)

    @property
    def is_lit(self) -> bool:
        return self.is_on

    @is_lit.setter
    def is_lit(self, value: bool) -> None:
        self.set_state(value)

    def shape(self):
        from PySide6.QtGui import QPainterPath
        from PySide6.QtCore import QRectF
        path = QPainterPath()
        path.addEllipse(QRectF(-12, -18, 24, 24)) # Bulb
        path.addRect(QRectF(-14, 4, 28, 4)) # Base
        path.addRect(QRectF(-8, 8, 4, 30)) # Left leg
        path.addRect(QRectF(4, 8, 4, 30)) # Right leg
        return path

    def boundingRect(self) -> QRectF:
        r = 38 if self.is_on else 22
        return QRectF(-r, -18, 2 * r, 66)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        cdata = self.COLOR_MAP.get(self.color_name, self.COLOR_MAP["red"])
        r_c, g_c, b_c = cdata["tint"]

        # 1. Halo lumineux volumétrique si allumée
        if self.is_on:
            glow = QRadialGradient(0, 0, 36)
            glow.setColorAt(0.0, QColor(r_c, g_c, b_c, 210))
            glow.setColorAt(0.4, QColor(r_c, g_c, b_c, 90))
            glow.setColorAt(1.0, QColor(r_c, g_c, b_c, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(0, 0), 36, 36)

        # 2. Pattes métalliques cylindriques avec occlusion lors de l'insertion
        self._paint_leads(painter)

        # 3. Électrodes métalliques internes visibles par transparence
        self._paint_internal_frame(painter, cdata)

        # 4. Bulbe époxy 5 mm (Dôme hémisphérique + collerette à méplat)
        self._paint_epoxy_body(painter, cdata)

        # 5. Reflet spéculaire brillant (lumière de laboratoire réfléchie sur l'époxy)
        self._paint_specular_highlight(painter)

    def _paint_leads(self, painter: QPainter):
        """Pattes métalliques argentées sortant sous la base avec occlusion de profondeur sous la plaque."""
        lead_grad = QLinearGradient(-1.0, 0, 1.0, 0)
        lead_grad.setColorAt(0.0, QColor("#475569"))
        lead_grad.setColorAt(0.35, QColor("#f1f5f9"))
        lead_grad.setColorAt(0.7, QColor("#cbd5e1"))
        lead_grad.setColorAt(1.0, QColor("#334155"))

        pen_lead = QPen(QBrush(lead_grad), 1.8, Qt.SolidLine, Qt.FlatCap)
        painter.setBrush(Qt.NoBrush)

        # --- 1. Patte Anode (+) ---
        # Si insérée, la portion sous la plaque (depth=8px) disparaît sous la surface (y=25.5)
        # Si libre, la patte se prolonge sur toute sa longueur physique
        target_y_a = 25.5 if self.anode_pin.is_inserted else 25.5 + 8.0

        path_a = QPainterPath()
        path_a.moveTo(-2.5, 8.0)
        path_a.cubicTo(-2.5, 14.0, 0.0, 16.0, 0.0, 21.0)
        path_a.lineTo(0.0, target_y_a)

        painter.setPen(pen_lead)
        painter.drawPath(path_a)

        if self.anode_pin.is_inserted:
            # Bague d'insertion et ombre de pénétration au ras de l'alvéole
            painter.setPen(QPen(QColor("#1e293b"), 0.6))
            painter.setBrush(QBrush(QColor("#cbd5e1")))
            painter.drawRect(QRectF(-1.0, 23.5, 2.0, 2.0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(15, 23, 42, 180)))
            painter.drawRect(QRectF(-1.2, 25.0, 2.4, 0.8))
        else:
            # Pointe biseautée métallique libre
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#cbd5e1")))
            painter.drawPolygon([QPointF(-0.9, target_y_a), QPointF(0.9, target_y_a), QPointF(0.0, target_y_a + 2.0)])

        # --- 2. Patte Cathode (-) ---
        target_y_c = 34.0 if self.cathode_pin.is_inserted else 34.0 + 8.0

        path_c = QPainterPath()
        path_c.moveTo(2.5, 8.0)
        path_c.cubicTo(2.5, 15.0, 0.0, 20.0, 0.0, 28.0)
        path_c.lineTo(0.0, target_y_c)

        painter.setPen(pen_lead)
        painter.drawPath(path_c)

        if self.cathode_pin.is_inserted:
            # Bague d'insertion et ombre de pénétration au ras de l'alvéole 2
            painter.setPen(QPen(QColor("#1e293b"), 0.6))
            painter.setBrush(QBrush(QColor("#cbd5e1")))
            painter.drawRect(QRectF(-1.0, 32.0, 2.0, 2.0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(15, 23, 42, 180)))
            painter.drawRect(QRectF(-1.2, 33.5, 2.4, 0.8))
        else:
            # Pointe biseautée métallique libre
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#cbd5e1")))
            painter.drawPolygon([QPointF(-0.9, target_y_c), QPointF(0.9, target_y_c), QPointF(0.0, target_y_c + 2.0)])

    def _paint_internal_frame(self, painter: QPainter, cdata: dict):
        """Structure d'électrodes internes (Enclume / Anvil côté cathode et Tige / Post côté anode)."""
        lead_col = QColor("#cbd5e1") if not self.is_on else QColor("#fef08a")
        painter.setPen(QPen(lead_col, 1.2))

        # Tige anode (gauche)
        painter.drawLine(-4, 9, -4, 0)

        # Enclume cathode (droite, grande pièce trapézoïdale)
        anvil = QPainterPath()
        anvil.moveTo(4, 9)
        anvil.lineTo(4, 1)
        anvil.lineTo(1, -2)
        anvil.lineTo(4, -5)
        anvil.lineTo(5, -5)
        anvil.lineTo(5, 9)
        anvil.closeSubpath()
        painter.setBrush(QBrush(lead_col))
        painter.drawPath(anvil)

        # Puce semi-conductrice (die) au creux de l'enclume
        if self.is_on:
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(2, -3), 1.8, 1.8)

    def _paint_epoxy_body(self, painter: QPainter, cdata: dict):
        """Dessine le corps en résine époxy 5 mm avec dégradé translucide et méplat."""
        r_c, g_c, b_c = cdata["tint"]

        # Tracé du bulbe (Dôme supérieur arrondi + collerette à la base)
        bulb_path = QPainterPath()
        bulb_path.moveTo(-9, 5)
        bulb_path.arcTo(QRectF(-9, -14, 18, 18), 180, -180) # Dôme hémisphérique
        bulb_path.lineTo(9, 7)
        bulb_path.lineTo(10.5, 7) # Collerette droite (méplat : plus court)
        bulb_path.lineTo(10.5, 9)
        bulb_path.lineTo(-11, 9)  # Collerette gauche normale
        bulb_path.lineTo(-11, 7)
        bulb_path.lineTo(-9, 7)
        bulb_path.closeSubpath()

        # Dégradé volumétrique de couleur
        epoxy_grad = QRadialGradient(-2, -5, 15)
        if self.is_on:
            epoxy_grad.setColorAt(0.0, QColor("#ffffff"))
            epoxy_grad.setColorAt(0.25, QColor(r_c, g_c, b_c, 245))
            epoxy_grad.setColorAt(0.8, QColor(cdata["glow"]))
            epoxy_grad.setColorAt(1.0, QColor(cdata["dark"]))
        else:
            epoxy_grad.setColorAt(0.0, QColor(r_c, g_c, b_c, 160))
            epoxy_grad.setColorAt(0.6, QColor(r_c, g_c, b_c, 200))
            epoxy_grad.setColorAt(1.0, QColor(cdata["dark"]))

        painter.setPen(QPen(QColor(cdata["dark"]), 1))
        painter.setBrush(QBrush(epoxy_grad))
        painter.drawPath(bulb_path)

    def _paint_specular_highlight(self, painter: QPainter):
        """Reflet spéculaire incurvé le long du dôme en verre/époxy."""
        spec_path = QPainterPath()
        spec_path.moveTo(-6, -10)
        spec_path.quadTo(-1, -12, 4, -10)
        spec_path.quadTo(-1, -10.5, -6, -10)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 170)))
        painter.drawPath(spec_path)

        # Petit éclat ponctuel en haut à gauche
        painter.drawEllipse(QPointF(-4, -6), 1.2, 1.2)

    def set_state(self, is_on: bool):
        if self.is_on != is_on:
            self.prepareGeometryChange()
            self.is_on = is_on
            self.brightness = 1.0 if is_on else 0.0
            self.update()

    def set_brightness(self, value: float):
        self.prepareGeometryChange()
        self.is_on = value > 0.0
        self.brightness = value
        self.update()
