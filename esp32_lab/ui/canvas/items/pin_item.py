"""
Point d'ancrage graphique pour une broche (PinAnchorItem)
Permet de connecter visuellement les fils de liaison
"""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject


class PinAnchorItem(QGraphicsObject):
    pin_clicked = Signal(object) # self

    def __init__(self, owner_id: str, pin_id: str, pin_name: str, parent=None):
        super().__init__(parent)
        self.owner_id = owner_id
        self.pin_id = pin_id
        self.pin_name = pin_name
        self.label = pin_name
        self._radius = 5.0
        self._is_hovered = False
        self._is_active = False

        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        # self.setToolTip(f"{pin_name} ({owner_id})")

    def boundingRect(self) -> QRectF:
        r = self._radius + 3
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        
        # Anneau extérieur
        if self._is_hovered:
            painter.setPen(QPen(QColor("#38bdf8"), 2))
            painter.setBrush(QBrush(QColor("#0284c7")))
        elif self._is_active:
            painter.setPen(QPen(QColor("#f59e0b"), 2))
            painter.setBrush(QBrush(QColor("#d97706")))
        else:
            painter.setPen(QPen(QColor("#64748b"), 1.5))
            painter.setBrush(QBrush(QColor("#334155")))
            
        painter.drawEllipse(QPointF(0, 0), self._radius, self._radius)
        
        # Point central cuivré / doré
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#fbbf24")))
        painter.drawEllipse(QPointF(0, 0), 2.0, 2.0)

    def hoverEnterEvent(self, event):
        self._is_hovered = True
        self.update()
        scene = self.scene()
        if scene and hasattr(scene, "inspect_pin"):
            try:
                info = scene.inspect_pin(self.owner_id, self.pin_id)
                lines = [
                    f"Component: {info['component']}",
                    f"Pin: {info['pin']}",
                    f"Inserted into: {info['inserted_into'] or 'Free'}",
                    f"Breadboard strip: {info['strip'] or 'None'}",
                    f"Connected holes: {', '.join(info['connected_holes']) if info['connected_holes'] else 'None'}",
                    f"Electrical Net: {info['net_id']}",
                ]
                # self.setToolTip("\n".join(lines)) # Disabled per user request
            except Exception:
                pass
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pin_clicked.emit(self)
            event.accept()
        else:
            super().mousePressEvent(event)

    def get_scene_center(self) -> QPointF:
        return self.scenePos()


class PhysicalPinItem(PinAnchorItem):
    """Broche physique réelle d'un composant traversant avec géométrie, profondeur et état d'insertion."""

    def __init__(
        self,
        owner_id: str,
        pin_id: str,
        pin_name: str,
        pin_length: float = 24.0,
        pin_thickness: float = 1.8,
        parent=None,
    ):
        super().__init__(owner_id, pin_id, pin_name, parent=parent)
        self.pin_length = float(pin_length)
        self.pin_thickness = float(pin_thickness)
        self.insertion_depth = 0.0
        self.associated_hole_id: str | None = None
        self.state: str = "FREE"  # FREE, APPROACHING, ALIGNED, INSERTING, INSERTED, REMOVING

    @property
    def is_inserted(self) -> bool:
        return self.insertion_depth > 0.0 and self.state == "INSERTED"

    @property
    def visible_length(self) -> float:
        """Portion de la broche restant visible au-dessus de la surface de la platine."""
        return max(0.0, self.pin_length - self.insertion_depth)

    @property
    def inserted_length(self) -> float:
        """Portion de la broche insérée à l'intérieur de l'alvéole."""
        return self.insertion_depth

    def set_inserted(self, hole_id: str, depth: float = 8.0):
        """Marque la broche comme insérée dans un trou avec une profondeur d'insertion."""
        self.associated_hole_id = hole_id
        self.insertion_depth = float(depth)
        self.state = "INSERTED"
        self.update()
        if self.parentItem():
            self.parentItem().update()

    def set_removed(self):
        """Restaure la broche à l'état libre avec sa longueur totale visible."""
        self.associated_hole_id = None
        self.insertion_depth = 0.0
        self.state = "FREE"
        self.update()
        if self.parentItem():
            self.parentItem().update()

    def set_state(self, state: str):
        self.state = state
        self.update()

    def mousePressEvent(self, event):
        if self.is_inserted:
            event.ignore()
            return

        super().mousePressEvent(event)

    def paint(self, painter, option, widget=None):
        """Rendu d'une broche physique : aucun cercle schématique au repos ou une fois insérée."""
        if self.is_inserted:
            # La broche est immergée dans l'alvéole de la plaque : aucun symbole flottant
            return

        if self._is_active:
            # Halo d'interaction discret lors de la création d'un câble
            painter.setRenderHint(painter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#f59e0b"), 1.5))
            painter.setBrush(QBrush(QColor(245, 158, 11, 130)))
            painter.drawEllipse(QPointF(0, 0), 3.0, 3.0)
        elif self._is_hovered:
            # Halo de survol discret pour le raccordement
            painter.setRenderHint(painter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#38bdf8"), 1.5))
            painter.setBrush(QBrush(QColor(56, 189, 248, 130)))
            painter.drawEllipse(QPointF(0, 0), 3.0, 3.0)
        else:
            # Au repos : pas de point schématique flottant, le composant dessine ses pattes métalliques réalistes
            pass

    def get_geometry(self) -> dict:
        """Retourne la géométrie et l'état physique complets de la broche."""
        return {
            "pin_id": self.pin_id,
            "pin_length": self.pin_length,
            "pin_thickness": self.pin_thickness,
            "insertion_depth": self.insertion_depth,
            "visible_length": self.visible_length,
            "inserted_length": self.inserted_length,
            "is_inserted": self.is_inserted,
            "associated_hole_id": self.associated_hole_id,
            "state": self.state,
        }


