"""
Rendu graphique ultra-réaliste d'un fil de raccordement flexible (Jumper Wire Dupont)
Gaine en PVC souple avec ombrage cylindrique, flèche de courbure naturelle (spline de Bézier),
ombre portée douce sur le plan de travail, et manchons connecteurs Dupont moulés aux extrémités.
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QGraphicsPathItem


class WireGraphicsItem(QGraphicsPathItem):
    """Représentation physique réaliste d'un câble de liaison souple avec embouts Dupont."""

    def __init__(self, connection_id: str, color: str = "#ef4444", parent=None):
        super().__init__(parent)
        self.connection_id = connection_id
        self.color_str = color
        self.start_pos = QPointF(0, 0)
        self.end_pos = QPointF(0, 0)
        self._is_hovered = False

        self.setZValue(10) # Les câbles passent au-dessus des composants
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)

        self._active_terminal: str | None = None
        self._hovered_terminal: str | None = None
        self.is_orthogonal: bool = False
        self.start_gender: str = "male"
        self.end_gender: str = "male"
        self._update_tooltip()
        self.update_path()

    def set_terminal_genders(self, start_gender: str = "male", end_gender: str = "male"):
        self.start_gender = start_gender
        self.end_gender = end_gender
        self._update_tooltip()
        self.update()

    def _update_tooltip(self):
        if self.start_gender == "male" and self.end_gender == "male":
            type_str = "Mâle - Mâle (M-M)"
        elif self.start_gender == "female" and self.end_gender == "female":
            type_str = "Femelle - Femelle (F-F)"
        else:
            type_str = "Mâle - Femelle (M-F)"
        self.setToolTip(f"Câble Dupont {type_str}\nCouleur : {self.color_str}\n(Clic droit pour options)")

    def set_orthogonal_mode(self, enabled: bool):
        if self.is_orthogonal != enabled:
            self.is_orthogonal = bool(enabled)
            self.update_path()

    def set_endpoints(self, start: QPointF, end: QPointF):
        self.start_pos = start
        self.end_pos = end
        self.update_path()

    def set_terminal_pos(self, terminal: str, pos: QPointF):
        """Met à jour temporairement la position d'un embout lors d'un glisser-déposer."""
        if terminal == "start":
            self.start_pos = pos
        elif terminal == "end":
            self.end_pos = pos
        self.update_path()

    def get_terminal_at(self, scene_pos: QPointF, tolerance: float = 12.0) -> str | None:
        """Détecte si une position globale se trouve au-dessus de l'embout de départ ou d'arrivée."""
        d_start = math.hypot(scene_pos.x() - self.start_pos.x(), scene_pos.y() - (self.start_pos.y() - 6.0))
        if d_start <= tolerance:
            return "start"

        d_end = math.hypot(scene_pos.x() - self.end_pos.x(), scene_pos.y() - (self.end_pos.y() - 6.0))
        if d_end <= tolerance:
            return "end"

        return None

    def update_path(self):
        path = QPainterPath()
        start_top = QPointF(self.start_pos.x(), self.start_pos.y() - 11.5)
        end_top = QPointF(self.end_pos.x(), self.end_pos.y() - 11.5)

        path.moveTo(start_top)

        if self.is_orthogonal:
            # Mode Manhattan (Segments orthogonaux à angle droit 90°)
            # Émergence verticale de 14px
            p1 = QPointF(start_top.x(), start_top.y() - 14.0)
            p2 = QPointF(end_top.x(), end_top.y() - 14.0)
            
            mid_y = min(p1.y(), p2.y()) - 10.0
            path.lineTo(p1.x(), mid_y)
            path.lineTo(p2.x(), mid_y)
            path.lineTo(end_top)
        else:
            # Mode Réaliste (Courbe de Bézier souple avec flèche de gravité)
            dx = end_top.x() - start_top.x()
            dy = end_top.y() - start_top.y()
            dist = math.hypot(dx, dy)

            sag = max(16.0, dist * 0.16)
            ctrl1 = QPointF(start_top.x() + dx * 0.25, start_top.y() + dy * 0.25 + sag)
            ctrl2 = QPointF(start_top.x() + dx * 0.75, end_top.y() - dy * 0.25 + sag)

            path.cubicTo(ctrl1, ctrl2, end_top)

        self.prepareGeometryChange()
        self.setPath(path)

    def shape(self) -> QPainterPath:
        """Définition de la forme cliquable : fil élargi (épaisseur 10px) + manchons Dupont."""
        stroker = QPainterPath()
        p = self.path()
        if not p.isEmpty():
            from PySide6.QtGui import QPainterPathStroker
            s = QPainterPathStroker()
            s.setWidth(10.0)
            stroker.addPath(s.createStroke(p))
        # Ajouter les boîtiers Dupont aux deux extrémités
        stroker.addRect(QRectF(self.start_pos.x() - 6.0, self.start_pos.y() - 14.0, 12.0, 16.0))
        stroker.addRect(QRectF(self.end_pos.x() - 6.0, self.end_pos.y() - 14.0, 12.0, 16.0))
        return stroker

    def boundingRect(self) -> QRectF:
        """Définit la zone de rafraîchissement incluant les manchons et l'ombre."""
        return self.shape().controlPointRect().adjusted(-5, -5, 5, 5)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        path = self.path()
        if path.isEmpty():
            return

        base_color = QColor(self.color_str)
        is_sel = self.isSelected()

        # 1. Ombre portée douce sur le plan de travail (décalée de 4px vers le bas)
        shadow_path = QPainterPath()
        shadow_path.addPath(path)
        painter.save()
        painter.translate(2, 4)
        painter.setPen(QPen(QColor(0, 0, 0, 40), 4.2, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(shadow_path)
        painter.restore()

        # 1b. Halo si sélectionné
        if is_sel:
            painter.setPen(QPen(QColor("#38bdf8"), 6.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawPath(path)

        # 2. Contour sombre du câble (définition de l'épaisseur cylindrique)
        dark_border = base_color.darker(170)
        painter.setPen(QPen(dark_border, 4.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)

        # 3. Gaine en PVC colorée principale
        fill_color = base_color if not (self._is_hovered or is_sel) else base_color.lighter(130)
        painter.setPen(QPen(fill_color, 3.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)

        # 4. Reflet spéculaire longitudinal (ligne de lumière blanche simulant le relief cylindrique)
        highlight_color = QColor(255, 255, 255, 120 if not self._is_hovered else 180)
        painter.setPen(QPen(highlight_color, 1.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)

        # 5. Manchons connecteurs rectangulaires Dupont aux deux extrémités
        self._paint_connector_boot(painter, self.start_pos, terminal_name="start")
        self._paint_connector_boot(painter, self.end_pos, terminal_name="end")

    def _paint_connector_boot(self, painter: QPainter, pos: QPointF, terminal_name: str = ""):
        """Dessine le boîtier surmoulé de la fiche Dupont (mâle ou femelle) avec surbrillance."""
        is_active = (self._active_terminal == terminal_name)
        is_hovered = (self._hovered_terminal == terminal_name)
        gender = self.start_gender if terminal_name == "start" else self.end_gender

        if gender == "male":
            # 1. Broche métallique étamée pénétrant directement dans l'alvéole cible (de y-2 à y+0.5)
            pin_grad = QLinearGradient(pos.x() - 1.0, 0, pos.x() + 1.0, 0)
            pin_grad.setColorAt(0.0, QColor("#64748b"))
            pin_grad.setColorAt(0.4, QColor("#f8fafc"))
            pin_grad.setColorAt(1.0, QColor("#475569"))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(pin_grad))
            painter.drawRoundedRect(QRectF(pos.x() - 0.9, pos.y() - 2.5, 1.8, 3.0), 0.4, 0.4)

            # 2. Boîtier plastique noir surmoulé Dupont mâle (5.6 x 9.5 px, au-dessus de la broche)
            boot_rect = QRectF(pos.x() - 2.8, pos.y() - 11.5, 5.6, 9.5)
        else:
            # 2. Connecteur FEMELLE Dupont :
            # Le manchon descend pour coiffer le picot mâle sans aiguille métallique apparente
            boot_rect = QRectF(pos.x() - 2.9, pos.y() - 11.5, 5.8, 12.0)

        boot_grad = QLinearGradient(boot_rect.left(), 0, boot_rect.right(), 0)

        if is_active:
            boot_grad.setColorAt(0.0, QColor("#0284c7"))
            boot_grad.setColorAt(0.5, QColor("#38bdf8"))
            boot_grad.setColorAt(1.0, QColor("#0369a1"))
        elif is_hovered:
            boot_grad.setColorAt(0.0, QColor("#3f3f46"))
            boot_grad.setColorAt(0.5, QColor("#71717a"))
            boot_grad.setColorAt(1.0, QColor("#3f3f46"))
        else:
            boot_grad.setColorAt(0.0, QColor("#27272a"))
            boot_grad.setColorAt(0.3, QColor("#3f3f46"))
            boot_grad.setColorAt(0.7, QColor("#27272a"))
            boot_grad.setColorAt(1.0, QColor("#18181b"))

        border_pen = QColor("#38bdf8") if (is_active or is_hovered) else QColor("#09090b")
        painter.setPen(QPen(border_pen, 1.0 if (is_active or is_hovered) else 0.6))
        painter.setBrush(QBrush(boot_grad))
        painter.drawRoundedRect(boot_rect, 1.0, 1.0)

        if gender == "female":
            # Receptacle d'insertion femelle au bas du connecteur
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#09090b")))
            painter.drawRect(QRectF(pos.x() - 1.2, pos.y() - 0.5, 2.4, 1.2))

        # Fenêtre d'ergot métallique Dupont (latch)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#09090b")))
        painter.drawRect(QRectF(pos.x() - 1.2, pos.y() - 8.5, 2.4, 3.2))
        painter.setBrush(QBrush(QColor("#94a3b8")))
        painter.drawRect(QRectF(pos.x() - 0.8, pos.y() - 7.5, 1.6, 1.8))

        # 3. Collerette anti-traction au sommet d'où émerge le fil
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#18181b")))
        painter.drawRoundedRect(QRectF(pos.x() - 1.6, pos.y() - 12.8, 3.2, 1.6), 0.6, 0.6)

    def hoverMoveEvent(self, event):
        scene_pos = event.scenePos()
        term = self.get_terminal_at(scene_pos)
        if term != self._hovered_terminal:
            self._hovered_terminal = term
            self.update()
        super().hoverMoveEvent(event)

    def hoverEnterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        self._hovered_terminal = None
        self.update()
        super().hoverLeaveEvent(event)
