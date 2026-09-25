"""
Rendu graphique ultra-réaliste d'une résistance traversante axiale 1/4W
Corps céramique renflé (dumbbell), anneaux de code couleur normalisés calculés
selon la valeur, bague de tolérance dorée métallisée, et fils axiaux étamés courbés.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QGraphicsObject

from .pin_item import PinAnchorItem, PhysicalPinItem


class ResistorGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'une résistance à couche de carbone 1/4W."""

    # Table des couleurs EIA pour le code des résistances
    DIGIT_COLORS = {
        0: QColor("#0f172a"), # Noir
        1: QColor("#78350f"), # Marron
        2: QColor("#dc2626"), # Rouge
        3: QColor("#ea580c"), # Orange
        4: QColor("#eab308"), # Jaune
        5: QColor("#16a34a"), # Vert
        6: QColor("#2563eb"), # Bleu
        7: QColor("#9333ea"), # Violet
        8: QColor("#64748b"), # Gris
        9: QColor("#ffffff"), # Blanc
    }

    def __init__(self, component_id: str, resistance_value: int = 220, parent=None):
        super().__init__(parent)
        self.component_id = component_id
        self.resistance_value = max(1, int(resistance_value))

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(3)

        # Deux broches physiques réelles (fils axiaux étamés)
        self.pin1 = PhysicalPinItem(component_id, "pin1", "Broche 1", pin_length=20.0, pin_thickness=1.8, parent=self)
        self.pin1.setPos(0, -25.5)

        self.pin2 = PhysicalPinItem(component_id, "pin2", "Broche 2", pin_length=20.0, pin_thickness=1.8, parent=self)
        self.pin2.setPos(0, 25.5)

    def shape(self):
        from PySide6.QtGui import QPainterPath
        from PySide6.QtCore import QRectF
        path = QPainterPath()
        path.addRect(QRectF(-6, -20, 12, 40)) # Body
        path.addRect(QRectF(-2, -40, 4, 20))  # Top leg
        path.addRect(QRectF(-2, 20, 4, 20))   # Bottom leg
        return path

    def boundingRect(self) -> QRectF:
        return QRectF(-16, -40, 32, 80)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Fils métalliques étamés (axiaux, pliés vers les alvéoles avec occlusion)
        self._paint_leads(painter)

        # 2. Corps céramique renflé 1/4W (Dumbbell body)
        self._paint_ceramic_body(painter)

        # 3. Anneaux de couleur calculés selon la valeur
        self._paint_color_bands(painter)

        # 4. Reflet spéculaire longitudinal (volume 3D cylindrique)
        self._paint_cylindrical_highlight(painter)

    def _paint_leads(self, painter: QPainter):
        """Fils en cuivre étamé argenté émergeant des embouts avec occlusion de profondeur sous la plaque."""
        lead_grad = QLinearGradient(-1.2, 0, 1.2, 0)
        lead_grad.setColorAt(0.0, QColor("#475569"))
        lead_grad.setColorAt(0.4, QColor("#f8fafc"))
        lead_grad.setColorAt(1.0, QColor("#334155"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(lead_grad))

        # --- 1. Patte haute (vers y = -25.5) ---
        target_y1 = -25.5 if self.pin1.is_inserted else -25.5 - 8.0
        h1 = abs(target_y1 - (-14.0))
        painter.drawRoundedRect(QRectF(-1.1, target_y1, 2.2, h1), 0.6, 0.6)

        if self.pin1.is_inserted:
            # Bague et ombre d'enfoncement dans le trou supérieur
            painter.setBrush(QBrush(QColor(15, 23, 42, 190)))
            painter.drawRect(QRectF(-1.4, -26.0, 2.8, 0.9))
        else:
            painter.setBrush(QBrush(QColor("#cbd5e1")))
            painter.drawPolygon([QPointF(-1.0, target_y1), QPointF(1.0, target_y1), QPointF(0.0, target_y1 - 2.0)])

        # --- 2. Patte basse (vers y = 25.5) ---
        target_y2 = 25.5 if self.pin2.is_inserted else 25.5 + 8.0
        h2 = abs(target_y2 - 14.0)
        painter.setBrush(QBrush(lead_grad))
        painter.drawRoundedRect(QRectF(-1.1, 14.0, 2.2, h2), 0.6, 0.6)

        if self.pin2.is_inserted:
            # Bague et ombre d'enfoncement dans le trou inférieur
            painter.setBrush(QBrush(QColor(15, 23, 42, 190)))
            painter.drawRect(QRectF(-1.4, 25.1, 2.8, 0.9))
        else:
            painter.setBrush(QBrush(QColor("#cbd5e1")))
            painter.drawPolygon([QPointF(-1.0, target_y2), QPointF(1.0, target_y2), QPointF(0.0, target_y2 + 2.0)])

    def _paint_ceramic_body(self, painter: QPainter):
        """Dessine le corps renflé caractéristique de la résistance 1/4W."""
        body_path = QPainterPath()
        # Profil profilé en haltère (renflement haut, taille cintrée, renflement bas)
        body_path.moveTo(-4.5, -14)
        body_path.arcTo(QRectF(-7, -14, 14, 6), 180, -180) # Bourrelet supérieur
        body_path.lineTo(5.5, -9)
        body_path.lineTo(5.0, 9)                            # Taille cylindrique
        body_path.arcTo(QRectF(-7, 8, 14, 6), 0, -180)     # Bourrelet inférieur
        body_path.lineTo(-5.0, 9)
        body_path.lineTo(-5.5, -9)
        body_path.closeSubpath()

        # Dégradé céramique beige/crème 3D (éclairage cylindrique latéral)
        body_grad = QLinearGradient(-7, 0, 7, 0)
        body_grad.setColorAt(0.0, QColor("#c2a884")) # Ombre gauche
        body_grad.setColorAt(0.2, QColor("#dfcbaf"))
        body_grad.setColorAt(0.45, QColor("#f4ede1")) # Ligne de lumière centrale
        body_grad.setColorAt(0.8, QColor("#d5bea0"))
        body_grad.setColorAt(1.0, QColor("#9c805c")) # Ombre droite

        painter.setPen(QPen(QColor("#9c805c"), 0.8))
        painter.setBrush(QBrush(body_grad))
        painter.drawPath(body_path)

    def _paint_color_bands(self, painter: QPainter):
        """Calcule et dessine les 4 anneaux normalisés (D1, D2, Mult, Tol)."""
        d1, d2, mult = self._compute_bands(self.resistance_value)

        # Hauteurs et largeurs des anneaux
        bands = [
            (-9.0, self.DIGIT_COLORS.get(d1, QColor("#dc2626")), 2.6),
            (-4.0, self.DIGIT_COLORS.get(d2, QColor("#dc2626")), 2.6),
            (1.5, self.DIGIT_COLORS.get(mult, QColor("#78350f")), 2.6),
            (7.5, QColor("#eab308"), 2.2), # Anneau doré 5%
        ]

        for y, col, h in bands:
            # Dégradé sur chaque anneau pour conserver le volume 3D
            b_grad = QLinearGradient(-6, 0, 6, 0)
            b_grad.setColorAt(0.0, col.darker(150))
            b_grad.setColorAt(0.4, col.lighter(130))
            b_grad.setColorAt(1.0, col.darker(160))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(b_grad))
            painter.drawRoundedRect(QRectF(-6.2, y, 12.4, h), 0.5, 0.5)

            # Si c'est la bague dorée, ajouter un éclat métallique
            if col == QColor("#eab308"):
                painter.setBrush(QBrush(QColor(255, 255, 255, 140)))
                painter.drawRect(QRectF(-1.0, y, 2.0, h))

    def _compute_bands(self, val: int) -> tuple[int, int, int]:
        s = str(val)
        if len(s) == 1:
            return 0, int(s[0]), 0
        d1 = int(s[0])
        d2 = int(s[1])
        mult = len(s) - 2
        return d1, d2, max(0, min(9, mult))

    def _paint_cylindrical_highlight(self, painter: QPainter):
        """Reflet de brillance vernie longitudinal."""
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 70)))
        painter.drawRoundedRect(QRectF(-1.0, -11, 2.0, 22), 1, 1)

    def set_value(self, val: int):
        self.resistance_value = max(1, int(val))
        self.update()
