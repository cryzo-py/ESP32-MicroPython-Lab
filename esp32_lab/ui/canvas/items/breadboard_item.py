"""
Rendu graphique ultra-réaliste d'une platine d'expérimentation (Breadboard 400 points)
Matériau ABS ivoire, encoches d'assemblage (dovetails), rails d'alimentation sérigraphiés,
numérotation des rangées, lettrage des colonnes, et alvéoles métalliques à pinces à ressort
avec points d'ancrage électriques interactifs (BreadboardHoleItem).
"""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
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


class HoleVisualState:
    FREE = "FREE"
    HOVERED = "HOVERED"
    VALID_PREVIEW = "VALID_PREVIEW"
    INVALID_PREVIEW = "INVALID_PREVIEW"
    OCCUPIED = "OCCUPIED"
    SELECTED = "SELECTED"


class BreadboardHoleItem(PinAnchorItem):
    """Trou d'insertion interactif de platine d'expérimentation."""

    def __init__(self, owner_id: str, hole_id: str, strip_id: str, label: str, parent=None):
        super().__init__(owner_id, hole_id, label, parent=parent)
        self.strip_id = strip_id  # ex: "row_15_left", "rail_l_minus", etc.
        self._radius = 3.2
        self.has_wire = False
        self.has_component_lead = False
        self.component_id: str | None = None
        self.lead_id: str | None = None
        self.highlight_strip = False
        self.is_collision = False
        self.is_preview = False
        self.visual_state = HoleVisualState.FREE

    @property
    def is_occupied(self) -> bool:
        return self.has_component_lead

    def set_visual_state(self, state: str):
        """Définit l'état visuel formel du trou."""
        self.visual_state = state
        self.is_preview = (state == HoleVisualState.VALID_PREVIEW)
        self.is_collision = (state == HoleVisualState.INVALID_PREVIEW)
        self.update()

    def set_preview_state(self, state: str | None):
        """Active un état de prévisualisation (VALID_PREVIEW / INVALID_PREVIEW) ou restaure l'état initial."""
        if state is None:
            self.visual_state = HoleVisualState.OCCUPIED if self.has_component_lead else HoleVisualState.FREE
            self.is_preview = False
            self.is_collision = False
        else:
            self.set_visual_state(state)
        self.update()

    def set_occupied(self, comp_id: str, lead_id: str):
        """Marque le trou comme OCCUPIED avec le composant et la broche associés."""
        self.has_component_lead = True
        self.component_id = comp_id
        self.lead_id = lead_id
        self.is_collision = False
        self.is_preview = False
        self.visual_state = HoleVisualState.OCCUPIED
        self.update()

    def set_free(self):
        """Libère le trou (état FREE)."""
        self.has_component_lead = False
        self.component_id = None
        self.lead_id = None
        self.is_collision = False
        self.is_preview = False
        self.visual_state = HoleVisualState.FREE
        self.update()

    def set_collision(self, active: bool):
        """Active ou désactive le retour visuel de collision (⚠ Trou occupé)."""
        self.is_collision = active
        self.visual_state = HoleVisualState.INVALID_PREVIEW if active else (
            HoleVisualState.OCCUPIED if self.has_component_lead else HoleVisualState.FREE
        )
        self.update()

    def set_preview_highlight(self, active: bool):
        """Active ou désactive la surbrillance de prévisualisation avant le drop."""
        self.set_preview_state(HoleVisualState.VALID_PREVIEW if active else None)

    def mousePressEvent(self, event):
        if self.is_occupied:
            event.ignore()
            return
        super().mousePressEvent(event)

    def boundingRect(self) -> QRectF:
        r = 6.5
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Retour de collision / INVALID_PREVIEW (Avertissement : trou occupé ou géométrie incompatible)
        if self.visual_state == HoleVisualState.INVALID_PREVIEW or self.is_collision:
            painter.setPen(QPen(QColor("#ef4444"), 1.5, Qt.DashLine))
            painter.setBrush(QBrush(QColor(239, 68, 68, 60)))
            painter.drawEllipse(QPointF(0, 0), 4.8, 4.8)
            return

        # 1b. Prévisualisation de snap valide VALID_PREVIEW avant drop
        if self.visual_state == HoleVisualState.VALID_PREVIEW or self.is_preview:
            painter.setPen(QPen(QColor("#10b981"), 1.5, Qt.DashLine))
            painter.setBrush(QBrush(QColor(16, 185, 129, 50)))
            painter.drawEllipse(QPointF(0, 0), 4.8, 4.8)
            return

        # 2. Si survolé ou actif : halo lumineux discret d'aide à la connexion
        if self._is_hovered:
            painter.setPen(QPen(QColor("#38bdf8"), 1.5))
            painter.setBrush(QBrush(QColor(56, 189, 248, 70)))
            painter.drawEllipse(QPointF(0, 0), 4.6, 4.6)
        elif self._is_active:
            painter.setPen(QPen(QColor("#f59e0b"), 1.6))
            painter.setBrush(QBrush(QColor(245, 158, 11, 90)))
            painter.drawEllipse(QPointF(0, 0), 4.6, 4.6)
        elif self.highlight_strip:
            # Surbrillance discrète et pédagogique du strip sans aucun fil artificiel
            painter.setPen(QPen(QColor("#0ea5e9"), 1.0, Qt.DashLine))
            painter.setBrush(QBrush(QColor(14, 165, 233, 30)))
            painter.drawEllipse(QPointF(0, 0), 4.0, 4.0)
        elif self.has_component_lead:
            # Rendu physique : patte métallique pénétrant dans la pince à ressort du trou
            # Fond sombre de la cavité sous la surface
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#0f1216")))
            painter.drawRoundedRect(QRectF(-1.8, -1.8, 3.6, 3.6), 0.4, 0.4)

            # Lames de la pince à ressort enserrant fermement la broche
            painter.setBrush(QBrush(QColor("#808a96")))
            painter.drawRect(QRectF(-1.6, -1.3, 0.6, 2.6))
            painter.drawRect(QRectF(1.0, -1.3, 0.6, 2.6))

            # Broche métallique étamée traversant l'ouverture
            pin_grad = QLinearGradient(-1.0, 0, 1.0, 0)
            pin_grad.setColorAt(0.0, QColor("#64748b"))
            pin_grad.setColorAt(0.35, QColor("#f1f5f9"))
            pin_grad.setColorAt(0.7, QColor("#cbd5e1"))
            pin_grad.setColorAt(1.0, QColor("#475569"))
            painter.setBrush(QBrush(pin_grad))
            painter.drawRoundedRect(QRectF(-1.0, -1.0, 2.0, 2.0), 0.3, 0.3)

            # Ombre d'occlusion au ras du rebord plastique supérieur
            painter.setBrush(QBrush(QColor(0, 0, 0, 120)))
            painter.drawRect(QRectF(-1.2, -1.5, 2.4, 0.6))
        elif self.has_wire:
            # Broche de connecteur cavalier DuPont insérée dans l'alvéole
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#0f1216")))
            painter.drawRoundedRect(QRectF(-1.8, -1.8, 3.6, 3.6), 0.4, 0.4)

            # Fiche métallique nickelée du cavalier
            pin_grad = QLinearGradient(-1.0, 0, 1.0, 0)
            pin_grad.setColorAt(0.0, QColor("#64748b"))
            pin_grad.setColorAt(0.4, QColor("#f8fafc"))
            pin_grad.setColorAt(1.0, QColor("#475569"))
            painter.setBrush(QBrush(pin_grad))
            painter.drawRoundedRect(QRectF(-1.1, -1.1, 2.2, 2.2), 0.4, 0.4)
        else:
            # Repos : laisse transparaître la douille photoréaliste de la plaque
            pass
            # Repos : discret pour laisser voir la douille photoréaliste de la plaque
            pass

    def hoverEnterEvent(self, event):
        parent_bb = self.parentItem()
        if isinstance(parent_bb, BreadboardGraphicsItem):
            parent_bb.set_strip_highlight(self.strip_id, True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        parent_bb = self.parentItem()
        if isinstance(parent_bb, BreadboardGraphicsItem):
            parent_bb.set_strip_highlight(self.strip_id, False)
        super().hoverLeaveEvent(event)



class BreadboardGraphicsItem(QGraphicsObject):
    """Représentation physique réaliste d'une platine d'expérimentation avec connectivité électrique."""

    ROW_START_Y = 28.0
    ROW_STEP_Y = 8.5
    COL_STEP_X = 8.5
    COL_LEFT_START_X = 46.0   # a, b, c, d, e
    COL_RIGHT_START_X = 118.0 # f, g, h, i, j
    RAIL_L_PLUS_X = 12.0
    RAIL_L_MINUS_X = 24.0
    RAIL_R_MINUS_X = 181.0
    RAIL_R_PLUS_X = 193.0

    def __init__(self, breadboard_id: str = "breadboard_1", parent=None):
        super().__init__(parent)
        self.breadboard_id = breadboard_id
        self.component_id = breadboard_id
        self.width = 205
        self.height = 310
        self.num_rows = 30

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(1)

        # Dictionnaires d'accès rapide aux alvéoles électriques
        self.hole_anchors: dict[str, BreadboardHoleItem] = {}
        self.strips: dict[str, list[BreadboardHoleItem]] = {}

        self._build_hole_grid()

    def itemChange(self, change, value):
        if change in (QGraphicsObject.ItemPositionChange, QGraphicsObject.ItemPositionHasChanged):
            scene = self.scene()
            if scene and hasattr(scene, "update_all_wires"):
                scene.update_all_wires()
        return super().itemChange(change, value)

    def contains_scene_pos(self, scene_pos: QPointF) -> bool:
        local_p = self.mapFromScene(scene_pos)
        return -25.0 <= local_p.x() <= self.width + 25.0 and -25.0 <= local_p.y() <= self.height + 25.0

    def _build_hole_grid(self):
        """Crée les alvéoles de contact électrique de la plaque 400 points."""
        col_letters_left = ["a", "b", "c", "d", "e"]
        col_letters_right = ["f", "g", "h", "i", "j"]

        for r in range(self.num_rows):
            row_num = r + 1
            py = self.ROW_START_Y + r * self.ROW_STEP_Y

            # 1. Rail d'alimentation Gauche (+ et -)
            # L+
            h_lp_id = f"rail_l_plus_{row_num}"
            strip_lp = "rail_left_plus"
            h_lp = BreadboardHoleItem(self.breadboard_id, h_lp_id, strip_lp, f"Rail L+ ({row_num})", parent=self)
            h_lp.setPos(self.RAIL_L_PLUS_X, py)
            self._register_hole(h_lp_id, strip_lp, h_lp)

            # L- (GND)
            h_lm_id = f"rail_l_minus_{row_num}"
            strip_lm = "rail_left_minus"
            h_lm = BreadboardHoleItem(self.breadboard_id, h_lm_id, strip_lm, f"Rail L- GND ({row_num})", parent=self)
            h_lm.setPos(self.RAIL_L_MINUS_X, py)
            self._register_hole(h_lm_id, strip_lm, h_lm)

            # 2. Rangées colonnes a..e (Bande de dérivation gauche)
            strip_left = f"row_{row_num}_left"
            for c_idx, c_name in enumerate(col_letters_left):
                px = self.COL_LEFT_START_X + c_idx * self.COL_STEP_X
                h_id = f"r{row_num}_{c_name}"
                h_item = BreadboardHoleItem(self.breadboard_id, h_id, strip_left, f"Ligne {row_num} Colonne {c_name.upper()}", parent=self)
                h_item.setPos(px, py)
                self._register_hole(h_id, strip_left, h_item)

            # 3. Rangées colonnes f..j (Bande de dérivation droite)
            strip_right = f"row_{row_num}_right"
            for c_idx, c_name in enumerate(col_letters_right):
                px = self.COL_RIGHT_START_X + c_idx * self.COL_STEP_X
                h_id = f"r{row_num}_{c_name}"
                h_item = BreadboardHoleItem(self.breadboard_id, h_id, strip_right, f"Ligne {row_num} Colonne {c_name.upper()}", parent=self)
                h_item.setPos(px, py)
                self._register_hole(h_id, strip_right, h_item)

            # 4. Rail d'alimentation Droit (- et +)
            # R- (GND)
            h_rm_id = f"rail_r_minus_{row_num}"
            strip_rm = "rail_right_minus"
            h_rm = BreadboardHoleItem(self.breadboard_id, h_rm_id, strip_rm, f"Rail R- GND ({row_num})", parent=self)
            h_rm.setPos(self.RAIL_R_MINUS_X, py)
            self._register_hole(h_rm_id, strip_rm, h_rm)

            # R+
            h_rp_id = f"rail_r_plus_{row_num}"
            strip_rp = "rail_right_plus"
            h_rp = BreadboardHoleItem(self.breadboard_id, h_rp_id, strip_rp, f"Rail R+ ({row_num})", parent=self)
            h_rp.setPos(self.RAIL_R_PLUS_X, py)
            self._register_hole(h_rp_id, strip_rp, h_rp)

    def _register_hole(self, hole_id: str, strip_id: str, item: BreadboardHoleItem):
        self.hole_anchors[hole_id] = item
        if strip_id not in self.strips:
            self.strips[strip_id] = []
        self.strips[strip_id].append(item)

    def get_pin_anchor(self, pin_id: str) -> BreadboardHoleItem | None:
        """Trouve une alvéole selon son identifiant standardisé ou alias."""
        if pin_id in self.hole_anchors:
            return self.hole_anchors[pin_id]

        # Aliases tolérants:
        pid = pin_id.lower().strip()
        # ex: "r10a" -> "r10_a"
        if len(pid) >= 3 and pid[0] == "r" and "_" not in pid and pid[-1] in "abcdefghij":
            alt = f"{pid[:-1]}_{pid[-1]}"
            if alt in self.hole_anchors:
                return self.hole_anchors[alt]
        # ex: "10_a" -> "r10_a"
        if not pid.startswith("r") and "_" in pid:
            alt = f"r{pid}"
            if alt in self.hole_anchors:
                return self.hole_anchors[alt]
        # ex: "rail_l_minus" -> "rail_l_minus_1"
        if pid in ("rail_l_minus", "gnd_l", "rail_minus"):
            return self.hole_anchors.get("rail_l_minus_15") or self.hole_anchors.get("rail_l_minus_1")
        if pid in ("rail_l_plus", "vcc_l", "rail_plus"):
            return self.hole_anchors.get("rail_l_plus_15") or self.hole_anchors.get("rail_l_plus_1")
        if pid in ("rail_r_minus", "gnd_r"):
            return self.hole_anchors.get("rail_r_minus_15") or self.hole_anchors.get("rail_r_minus_1")
        if pid in ("rail_r_plus", "vcc_r"):
            return self.hole_anchors.get("rail_r_plus_15") or self.hole_anchors.get("rail_r_plus_1")

        return None

    def set_strip_highlight(self, strip_id: str, highlight: bool):
        """Met en surbrillance éducative toute la bande conductrice de la plaque."""
        holes = self.strips.get(strip_id, [])
        for h in holes:
            h.highlight_strip = highlight
            h.update()

    def set_preview_states(self, valid_holes: list[str], invalid_holes: list[str] = None):
        """Met à jour les états visuels des trous cibles (VALID_PREVIEW / INVALID_PREVIEW)."""
        valid_set = set(valid_holes or [])
        invalid_set = set(invalid_holes or [])

        for h_id, hole in self.hole_anchors.items():
            if h_id in valid_set:
                hole.set_preview_state(HoleVisualState.VALID_PREVIEW)
            elif h_id in invalid_set:
                hole.set_preview_state(HoleVisualState.INVALID_PREVIEW)
            elif hole.is_preview or hole.is_collision or hole.visual_state in (HoleVisualState.VALID_PREVIEW, HoleVisualState.INVALID_PREVIEW):
                hole.set_preview_state(None)

    def clear_preview_highlights(self):
        """Efface toutes les surbrillances de prévisualisation de snap."""
        for hole in self.hole_anchors.values():
            if hole.is_preview or hole.is_collision or hole.visual_state in (HoleVisualState.VALID_PREVIEW, HoleVisualState.INVALID_PREVIEW):
                hole.set_preview_state(None)

    def highlight_preview_holes(self, hole_ids: list[str]):
        """Active la surbrillance de prévisualisation valide pour une liste d'alvéoles cibles."""
        self.set_preview_states(valid_holes=hole_ids, invalid_holes=[])

    def find_nearest_hole(self, scene_pos: QPointF, max_dist: float = 18.0) -> tuple[str, str, QPointF] | None:
        """Trouve l'alvéole la plus proche d'une coordonnée globale scène."""
        local_p = self.mapFromScene(scene_pos)
        best_dist_sq = max_dist * max_dist
        best_hole = None

        for hole_id, item in self.hole_anchors.items():
            hp = item.pos()
            dx = local_p.x() - hp.x()
            dy = local_p.y() - hp.y()
            dist_sq = dx * dx + dy * dy
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_hole = (hole_id, item.strip_id, self.mapToScene(hp))

        return best_hole

    def get_hole_scene_pos(self, hole_id: str) -> QPointF | None:
        item = self.get_pin_anchor(hole_id)
        if item:
            return item.scenePos()
        return None

    def boundingRect(self) -> QRectF:
        return QRectF(-10, -6, self.width + 20, self.height + 12)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Ombre portée douce sous la plaque
        shadow_rect = QRectF(2, 4, self.width - 4, self.height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 45)))
        painter.drawRoundedRect(shadow_rect, 6, 6)

        # 2. Encoches d'assemblage latérales (dovetail tabs et slots)
        painter.setBrush(QBrush(QColor("#eae7de")))
        painter.setPen(QPen(QColor("#c8c4b7"), 1))
        for y_tab in [60, 150, 240]:
            tab_path = QPainterPath()
            tab_path.moveTo(0, y_tab)
            tab_path.lineTo(-6, y_tab + 3)
            tab_path.lineTo(-6, y_tab + 17)
            tab_path.lineTo(0, y_tab + 20)
            tab_path.closeSubpath()
            painter.drawPath(tab_path)

        # 3. Corps principal en plastique ABS (dégradé blanc ivoire texturé)
        body_grad = QLinearGradient(0, 0, self.width, self.height)
        body_grad.setColorAt(0.0, QColor("#faf9f5"))
        body_grad.setColorAt(0.5, QColor("#f4f2ea"))
        body_grad.setColorAt(1.0, QColor("#ece8de"))

        painter.setPen(QPen(QColor("#c5c0b0"), 1.2))
        painter.setBrush(QBrush(body_grad))
        painter.drawRoundedRect(0, 0, self.width, self.height, 6, 6)

        # Biseau intérieur de la coque
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, self.width - 2, self.height - 2, 5, 5)

        # 4. Gouttière centrale (DIP IC divider trough) avec ombrage de profondeur
        cx = self.width / 2.0
        trough_width = 8.0
        trough_grad = QLinearGradient(cx - trough_width / 2, 0, cx + trough_width / 2, 0)
        trough_grad.setColorAt(0.0, QColor("#cfcac0"))
        trough_grad.setColorAt(0.25, QColor("#e2ded6"))
        trough_grad.setColorAt(0.75, QColor("#eae7df"))
        trough_grad.setColorAt(1.0, QColor("#bfb9ad"))

        painter.setPen(QPen(QColor("#b8b2a3"), 0.8))
        painter.setBrush(QBrush(trough_grad))
        painter.drawRoundedRect(cx - trough_width / 2, 16, trough_width, self.height - 32, 2, 2)

        # 5. Rails d'alimentation latéraux (+ Rouge / - Bleu)
        self._paint_power_rails(painter)

        # 6. Sérigraphie des repères
        self._paint_labels(painter)

        # 7. Grille d'alvéoles de contact
        self._paint_contact_sockets(painter)

        # 8. Logo de la platine sérigraphié
        font_brand = QFont("Arial", 6, QFont.Bold)
        painter.setFont(font_brand)
        painter.setPen(QColor("#9c9689"))
        painter.drawText(QRectF(15, 6, 60, 10), Qt.AlignCenter, "ESP32-LAB")
        painter.drawText(QRectF(self.width - 75, 6, 60, 10), Qt.AlignCenter, "MB-102")

    def _paint_power_rails(self, painter: QPainter):
        pen_red = QPen(QColor("#dc2626"), 1.8, Qt.SolidLine, Qt.RoundCap)
        pen_blue = QPen(QColor("#2563eb"), 1.8, Qt.SolidLine, Qt.RoundCap)

        # Rail gauche (+ rouge ext, - bleu int)
        painter.setPen(pen_red)
        painter.drawLine(12, 24, 12, self.height - 24)
        painter.setPen(pen_blue)
        painter.drawLine(24, 24, 24, self.height - 24)

        # Rail droit (- bleu int, + rouge ext)
        painter.setPen(pen_blue)
        painter.drawLine(self.width - 24, 24, self.width - 24, self.height - 24)
        painter.setPen(pen_red)
        painter.drawLine(self.width - 12, 24, self.width - 12, self.height - 24)

        # Symboles + et -
        font_sym = QFont("Arial", 8, QFont.Bold)
        painter.setFont(font_sym)

        # Haut
        painter.setPen(QColor("#dc2626"))
        painter.drawText(8, 20, "+")
        painter.drawText(self.width - 16, 20, "+")
        painter.setPen(QColor("#2563eb"))
        painter.drawText(21, 20, "-")
        painter.drawText(self.width - 29, 20, "-")

        # Bas
        painter.setPen(QColor("#dc2626"))
        painter.drawText(8, self.height - 10, "+")
        painter.drawText(self.width - 16, self.height - 10, "+")
        painter.setPen(QColor("#2563eb"))
        painter.drawText(21, self.height - 10, "-")
        painter.drawText(self.width - 29, self.height - 10, "-")

    def _paint_labels(self, painter: QPainter):
        font_num = QFont("Arial", 5, QFont.Normal)
        painter.setFont(font_num)
        painter.setPen(QColor("#8c867a"))

        for r in range(self.num_rows):
            row_num = r + 1
            py = self.ROW_START_Y + r * self.ROW_STEP_Y
            if row_num in (1, 5, 10, 15, 20, 25, 30):
                txt = str(row_num)
                painter.drawText(QRectF(31, py - 4, 10, 8), Qt.AlignCenter, txt)
                painter.drawText(QRectF(self.width - 41, py - 4, 10, 8), Qt.AlignCenter, txt)

        col_letters_left = ["a", "b", "c", "d", "e"]
        col_letters_right = ["f", "g", "h", "i", "j"]
        font_col = QFont("Arial", 5, QFont.Bold)
        painter.setFont(font_col)

        for c, let in enumerate(col_letters_left):
            px = self.COL_LEFT_START_X + c * self.COL_STEP_X
            painter.drawText(QRectF(px - 4, 16, 8, 8), Qt.AlignCenter, let)
            painter.drawText(QRectF(px - 4, self.height - 24, 8, 8), Qt.AlignCenter, let)

        for c, let in enumerate(col_letters_right):
            px = self.COL_RIGHT_START_X + c * self.COL_STEP_X
            painter.drawText(QRectF(px - 4, 16, 8, 8), Qt.AlignCenter, let)
            painter.drawText(QRectF(px - 4, self.height - 24, 8, 8), Qt.AlignCenter, let)

    def _paint_contact_sockets(self, painter: QPainter):
        for r in range(self.num_rows):
            py = self.ROW_START_Y + r * self.ROW_STEP_Y

            # Rails gauche
            self._draw_socket(painter, self.RAIL_L_PLUS_X, py)
            self._draw_socket(painter, self.RAIL_L_MINUS_X, py)

            # Colonnes a..e
            for c in range(5):
                px = self.COL_LEFT_START_X + c * self.COL_STEP_X
                self._draw_socket(painter, px, py)

            # Colonnes f..j
            for c in range(5):
                px = self.COL_RIGHT_START_X + c * self.COL_STEP_X
                self._draw_socket(painter, px, py)

            # Rails droit
            self._draw_socket(painter, self.RAIL_R_MINUS_X, py)
            self._draw_socket(painter, self.RAIL_R_PLUS_X, py)

    def _draw_socket(self, painter: QPainter, x: float, y: float):
        """Dessine une alvéole réaliste : chanfrein plastique + trou carré + lame métallique nickelée."""
        # 1. Chanfrein plastique d'entonnoir (chanfrein adouci dans l'ABS)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#d4cfc2")))
        painter.drawRoundedRect(QRectF(x - 2.6, y - 2.6, 5.2, 5.2), 0.6, 0.6)

        # Ligne de surbrillance supérieure du chanfrein
        painter.setBrush(QBrush(QColor(255, 255, 255, 120)))
        painter.drawRect(QRectF(x - 2.4, y - 2.6, 4.8, 0.5))

        # 2. Cavité sombre en profondeur (fond du puits plastique)
        painter.setBrush(QBrush(QColor("#111417")))
        painter.drawRoundedRect(QRectF(x - 1.8, y - 1.8, 3.6, 3.6), 0.4, 0.4)

        # 3. Lames métalliques de contact à ressort (lame gauche et lame droite séparées par fente)
        # Lame gauche
        painter.setBrush(QBrush(QColor("#78828e")))
        painter.drawRect(QRectF(x - 1.4, y - 1.3, 0.7, 2.6))
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawRect(QRectF(x - 1.4, y - 0.9, 0.4, 1.8))

        # Lame droite
        painter.setBrush(QBrush(QColor("#78828e")))
        painter.drawRect(QRectF(x + 0.7, y - 1.3, 0.7, 2.6))
        painter.setBrush(QBrush(QColor("#cbd5e1")))
        painter.drawRect(QRectF(x + 1.0, y - 0.9, 0.4, 1.8))

        # Fente d'insertion centrale et ombre de profondeur
        painter.setBrush(QBrush(QColor("#08090b")))
        painter.drawRect(QRectF(x - 0.6, y - 1.5, 1.2, 3.0))
