"""
Vue interactive QGraphicsView pour le circuit (CircuitView) avec zoom, pan fluide et Drag & Drop natif
"""

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsItem, QGraphicsObject

from .circuit_scene import CircuitScene
from .snap_engine import extract_pins


class CircuitView(QGraphicsView):
    def __init__(self, scene: CircuitScene, parent=None):
        super().__init__(scene, parent)
        self.circuit_scene = scene
        self.circuit_scene.is_lock_tool_active = False

        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # Activer le Drag & Drop natif
        self.setAcceptDrops(True)

        self._zoom_factor = 1.15
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-esp32-component") or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-esp32-component") or event.mimeData().hasText():
            event.acceptProposedAction()
            bb = self.circuit_scene.breadboard_item
            if bb:
                scene_pos = self.mapToScene(event.position().toPoint())
                if bb.contains_scene_pos(scene_pos):
                    comp_type = ""
                    if event.mimeData().hasFormat("application/x-esp32-component"):
                        comp_type = bytes(event.mimeData().data("application/x-esp32-component")).decode("utf-8")
                    elif event.mimeData().hasText():
                        comp_type = event.mimeData().text().strip()

                    # Simuler un item temporaire pour le preview des trous de placement
                    temp_item = getattr(self, "_drag_palette_item", None)
                    if not temp_item or getattr(temp_item, "_comp_type", "") != comp_type:
                        temp_item = self.circuit_scene._create_component_item(comp_type, f"tmp_{comp_type}")
                        temp_item._comp_type = comp_type
                        self._drag_palette_item = temp_item

                    preview = self.circuit_scene.preview_component_placement(temp_item, scene_pos)
                    if preview.valid:
                        bb.set_preview_states(valid_holes=preview.target_holes, invalid_holes=[])
                    else:
                        bb.set_preview_states(valid_holes=[], invalid_holes=preview.invalid_holes or preview.target_holes)
                else:
                    bb.clear_preview_highlights()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        bb = self.circuit_scene.breadboard_item
        if bb:
            bb.clear_preview_highlights()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        bb = self.circuit_scene.breadboard_item
        if bb:
            bb.clear_preview_highlights()

        comp_type = ""
        if event.mimeData().hasFormat("application/x-esp32-component"):
            comp_type = bytes(event.mimeData().data("application/x-esp32-component")).decode("utf-8")
        elif event.mimeData().hasText():
            comp_type = event.mimeData().text().strip()

        if comp_type:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.circuit_scene.add_component(comp_type, scene_pos)
            event.acceptProposedAction()
            return

        super().dropEvent(event)

    def wheelEvent(self, event):
        """Zoom centré sous le curseur de la souris"""
        if event.angleDelta().y() > 0:
            self.scale(self._zoom_factor, self._zoom_factor)
        else:
            self.scale(1.0 / self._zoom_factor, 1.0 / self._zoom_factor)
        event.accept()

    def mousePressEvent(self, event):
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        item = self.itemAt(pos)
        
        # Check Lock Tool
        if getattr(self.circuit_scene, "is_lock_tool_active", False) and event.button() == Qt.LeftButton:
            from esp32_lab.core.app_state import AppMode
            if getattr(self.circuit_scene, "interaction_policy", None) and self.circuit_scene.interaction_policy._app_state.mode == AppMode.TEACHER:
                clicked_id = None
                is_wire = False
                curr = item
                while curr:
                    if hasattr(curr, "component_id"):
                        clicked_id = curr.component_id
                        break
                    if hasattr(curr, "connection_id"):
                        clicked_id = curr.connection_id
                        is_wire = True
                        break
                    curr = curr.parentItem()
                if clicked_id:
                    self._open_lock_dialog(clicked_id, is_wire)
                    event.accept()
                    return

        # 1. Panning : Clic Molette OU Clic Gauche/Droit dans le vide
        if event.button() == Qt.MiddleButton or (not item and event.button() in (Qt.LeftButton, Qt.RightButton)):
            self._is_panning = True
            self._pan_start_x = event.position().x()
            self._pan_start_y = event.position().y()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        elif event.button() == Qt.RightButton:
            # Sinon, laisser passer pour le contextMenuEvent
            super().mousePressEvent(event)
            return
        else:
            bb = self.circuit_scene.breadboard_item
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            scene_pos = self.mapToScene(pos)

            # 1. Vérifier en priorité si on clique sur un embout Dupont de fil de connexion
            self._dragging_wire_terminal = None
            for wire in self.circuit_scene.wire_items.values():
                term = wire.get_terminal_at(scene_pos)
                if term:
                    if getattr(self.circuit_scene, "interaction_policy", None) and not self.circuit_scene.interaction_policy.can_move(wire.connection_id):
                        # Locked wire! Ignore drag.
                        continue
                    
                    conn = next((c for c in self.circuit_scene.connections if c.id == wire.connection_id), None)
                    old_comp = (conn.from_component if term == "start" else conn.to_component) if conn else ""
                    old_pin = (conn.from_pin if term == "start" else conn.to_pin) if conn else ""
                    self._dragging_wire_terminal = {
                        "wire": wire,
                        "terminal": term,
                        "original_start": wire.start_pos,
                        "original_end": wire.end_pos,
                        "old_comp_id": old_comp,
                        "old_pin_id": old_pin,
                    }
                    wire._active_terminal = term
                    wire.update()
                    event.accept()
                    return

            # 2. Identifier le composant ciblé sous le curseur
            item = self.itemAt(pos)
            top_item = item
            while top_item and top_item != bb and not (hasattr(top_item, "component_id") and (top_item.flags() & QGraphicsObject.ItemIsMovable)):
                top_item = top_item.parentItem()

            if top_item and top_item != bb and hasattr(top_item, "component_id"):
                self._dragged_item = top_item
                self._drag_start_pos = event.position()
                self._is_dragging_component = False

                top_item._last_valid_pos = top_item.pos()
                top_item._last_valid_scene_pos = top_item.scenePos()
                top_item._last_valid_parent = top_item.parentItem()
                top_item._last_valid_holes = dict(self.circuit_scene.topology.get_component_holes(top_item.component_id))
                top_item._last_valid_rotation = top_item.rotation()
                top_item._was_inserted = (top_item.parentItem() == bb)

                if not top_item.isSelected():
                    self.circuit_scene.clearSelection()
                    top_item.setSelected(True)
            else:
                self._dragged_item = None
                self._is_dragging_component = False

            super().mousePressEvent(event)

            for sel_it in self.circuit_scene.selectedItems():
                if hasattr(sel_it, "component_id") and sel_it != bb:
                    if not hasattr(sel_it, "_last_valid_pos") or sel_it._last_valid_pos is None:
                        sel_it._last_valid_pos = sel_it.pos()
                        sel_it._last_valid_scene_pos = sel_it.scenePos()
                        sel_it._last_valid_parent = sel_it.parentItem()
                        sel_it._last_valid_holes = dict(self.circuit_scene.topology.get_component_holes(sel_it.component_id))
                        sel_it._last_valid_rotation = sel_it.rotation()
                        sel_it._was_inserted = (sel_it.parentItem() == bb)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            dx = event.position().x() - self._pan_start_x
            dy = event.position().y() - self._pan_start_y
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - dx))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - dy))
            self._pan_start_x = event.position().x()
            self._pan_start_y = event.position().y()
            super().mouseMoveEvent(event)
            self.circuit_scene.update_all_wires()
            return

        super().mouseMoveEvent(event)

        # 1. Gestion du déplacement interactif d'un embout de fil
        wire_drag = getattr(self, "_dragging_wire_terminal", None)
        if wire_drag and (event.buttons() & Qt.LeftButton):
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            scene_pos = self.mapToScene(pos)
            wire = wire_drag["wire"]
            terminal = wire_drag["terminal"]

            # Trouver si une ancre ou un trou est proche pour l'aimantation visuelle
            target_anchor = self.circuit_scene.find_pin_anchor_near_scene_pos(scene_pos, max_dist=18.0)
            if target_anchor:
                wire.set_terminal_pos(terminal, target_anchor.get_scene_center())
                bb = self.circuit_scene.breadboard_item
                if bb and hasattr(target_anchor, "hole_id"):
                    bb.set_preview_states(valid_holes=[target_anchor.hole_id], invalid_holes=[])
            else:
                wire.set_terminal_pos(terminal, scene_pos)
                bb = self.circuit_scene.breadboard_item
                if bb:
                    bb.clear_preview_highlights()
            return

        # 2. Gestion du déplacement de composant
        if event.buttons() & Qt.LeftButton:
            bb = self.circuit_scene.breadboard_item
            target_item = getattr(self, "_dragged_item", None)
            if not target_item or not hasattr(target_item, "component_id") or target_item == bb:
                sel = [it for it in self.circuit_scene.selectedItems() if it != bb and hasattr(it, "component_id")]
                target_item = sel[0] if sel else None

            if target_item:
                if hasattr(self, "_drag_start_pos") and not getattr(self, "_is_dragging_component", False):
                    if (event.position() - self._drag_start_pos).manhattanLength() > 2:
                        self._is_dragging_component = True
                        if getattr(target_item, "_was_inserted", False):
                            self.circuit_scene._remove_component_from_breadboard(target_item)

                if getattr(self, "_is_dragging_component", False):
                    scene_pos = target_item.scenePos()
                    if bb and bb.contains_scene_pos(scene_pos):
                        preview = self.circuit_scene.preview_component_placement(target_item, scene_pos)
                        if preview.valid:
                            bb.set_preview_states(valid_holes=preview.target_holes, invalid_holes=[])
                        else:
                            bb.set_preview_states(valid_holes=[], invalid_holes=preview.invalid_holes or preview.target_holes)
                    elif bb:
                        bb.clear_preview_highlights()

            self.circuit_scene.update_all_wires()

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.MiddleButton, Qt.RightButton) and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

        bb = self.circuit_scene.breadboard_item
        if bb:
            bb.clear_preview_highlights()

        # 1. Finalisation du déplacement d'embout de fil
        wire_drag = getattr(self, "_dragging_wire_terminal", None)
        if wire_drag:
            wire = wire_drag["wire"]
            terminal = wire_drag["terminal"]
            wire._active_terminal = None

            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            scene_pos = self.mapToScene(pos)

            # Chercher l'ancre sous le point de relâchement
            target_anchor = self.circuit_scene.find_pin_anchor_near_scene_pos(scene_pos, max_dist=20.0)
            if target_anchor:
                # Ancre valide : reconnecter
                new_owner = target_anchor.owner_id
                new_pin = target_anchor.pin_id
                old_comp = wire_drag.get("old_comp_id")
                old_pin = wire_drag.get("old_pin_id")

                if new_owner != old_comp or new_pin != old_pin:
                    self.circuit_scene.reconnect_wire_terminal(wire.connection_id, terminal, new_owner, new_pin)
                    if hasattr(self.circuit_scene, "undo_stack") and self.circuit_scene.undo_stack:
                        from .undo_commands import MoveWireTerminalCommand
                        cmd = MoveWireTerminalCommand(
                            self.circuit_scene,
                            wire.connection_id,
                            terminal,
                            old_comp,
                            old_pin,
                            new_owner,
                            new_pin,
                            initial_applied=True,
                        )
                        self.circuit_scene.undo_stack.push(cmd)
            else:
                # Relâché dans le vide : réinitialiser aux coordonnées de l'ancienne ancre
                self.circuit_scene._update_wire_geometry(wire.connection_id)

            self._dragging_wire_terminal = None
            wire.update()
            if bb:
                self.circuit_scene.update_all_wires()
            event.accept()
            return

        # 2. Finalisation du déplacement de composant
        target_item = getattr(self, "_dragged_item", None)
        was_dragging = getattr(self, "_is_dragging_component", False)
        self._is_dragging_component = False
        self._dragged_item = None

        if not target_item or target_item == bb or not hasattr(target_item, "component_id"):
            sel = [it for it in self.circuit_scene.selectedItems() if it != bb and hasattr(it, "component_id")]
            target_item = sel[0] if sel else None

        if target_item and was_dragging and hasattr(target_item, "component_id") and target_item != bb:
            scene_pos = target_item.scenePos()
            is_on_bb = bb.contains_scene_pos(scene_pos) if bb else False

            old_pos = getattr(target_item, "_last_valid_pos", target_item.pos())
            old_parent = getattr(target_item, "_last_valid_parent", None)
            old_holes = getattr(target_item, "_last_valid_holes", {})
            old_rot = getattr(target_item, "_last_valid_rotation", target_item.rotation())

            if is_on_bb and bb:
                preview = self.circuit_scene.preview_component_placement(target_item, scene_pos)
                if preview.valid:
                    self.circuit_scene.commit_component_placement(target_item, preview)
                else:
                    self.circuit_scene.reject_component_placement(target_item, preview)
            else:
                if bb and target_item.parentItem() == bb:
                    target_item.setParentItem(None)
                    target_item.setPos(scene_pos)
                target_item._last_valid_pos = scene_pos
                target_item._last_valid_parent = None
                target_item._last_valid_holes = {}
                target_item._was_inserted = False

            new_pos = target_item.pos()
            new_parent = target_item.parentItem()
            new_holes = dict(self.circuit_scene.topology.get_component_holes(target_item.component_id))
            new_rot = target_item.rotation()

            if (old_pos != new_pos or old_parent != new_parent or old_holes != new_holes or old_rot != new_rot):
                if hasattr(self.circuit_scene, "undo_stack") and self.circuit_scene.undo_stack:
                    from .undo_commands import MoveComponentCommand
                    cmd = MoveComponentCommand(
                        self.circuit_scene,
                        target_item.component_id,
                        old_pos,
                        new_pos,
                        old_parent,
                        new_parent,
                        old_holes,
                        new_holes,
                        old_rot,
                        new_rot,
                        initial_applied=True,
                    )
                    self.circuit_scene.undo_stack.push(cmd)

        if bb:
            self.circuit_scene.update_all_wires()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.circuit_scene.rotate_selected_component(90.0)
            event.accept()
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.circuit_scene.delete_selected_items()
            event.accept()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        from .wire_item import WireGraphicsItem
        from esp32_lab.core.app_state import AppMode

        # Vérifier si on est en mode enseignant
        is_teacher = getattr(self.circuit_scene, "interaction_policy", None) and self.circuit_scene.interaction_policy._app_state.mode == AppMode.TEACHER

        scene_pos = self.mapToScene(event.pos())
        clicked_wire = None
        # 1. Vérifier si un fil ou un embout est cliqué
        for wire in self.circuit_scene.wire_items.values():
            if wire.contains(wire.mapFromScene(scene_pos)) or wire.get_terminal_at(scene_pos, tolerance=15.0):
                clicked_wire = wire
                break

        if clicked_wire:
            menu = QMenu(self)
            color_menu = menu.addMenu("🎨 Changer la couleur du fil")
            wire_colors = [
                ("🔴 Rouge (VCC / 3.3V / 5V)", "#ef4444"),
                ("⚫ Noir (GND / Masse)", "#18181b"),
                ("🔵 Bleu (Signal / GPIO)", "#3b82f6"),
                ("🟢 Vert (Signal)", "#22c55e"),
                ("🟡 Jaune (Signal / Horloge)", "#eab308"),
                ("🟠 Orange (Signal)", "#f97316"),
                ("🟣 Violet (Signal)", "#a855f7"),
                ("⚪ Blanc (Signal)", "#f8fafc"),
            ]
            for color_name, color_hex in wire_colors:
                act = color_menu.addAction(color_name)
                act.triggered.connect(lambda checked=False, w=clicked_wire, c=color_hex: self._change_wire_color(w, c))

            if is_teacher:
                menu.addSeparator()
                act_lock_wire = menu.addAction("🔒 Verrouiller le fil (Prof)")
            else:
                act_lock_wire = None

            act_del_wire = menu.addAction("🗑️ Supprimer le fil (Suppr)")
            action = menu.exec(event.globalPos())
            if action == act_del_wire:
                clicked_wire.setSelected(True)
                self.circuit_scene.delete_selected_items()
            elif act_lock_wire and action == act_lock_wire:
                self._open_lock_dialog(clicked_wire.connection_id, is_wire=True)
            event.accept()
            return

        item = self.itemAt(event.pos())
        if item:
            top_item = item
            bb = self.circuit_scene.breadboard_item
            while top_item and top_item != bb and not hasattr(top_item, "component_id"):
                top_item = top_item.parentItem()

            if top_item and top_item != bb:
                menu = QMenu(self)
                act_rot = menu.addAction("🔄 Faire pivoter de 90° (R)")
                
                if is_teacher:
                    menu.addSeparator()
                    act_lock = menu.addAction("🔒 Verrouiller le composant (Prof)")
                else:
                    act_lock = None
                    
                act_del = menu.addAction("🗑️ Supprimer (Suppr)")

                action = menu.exec(event.globalPos())
                if action == act_rot:
                    top_item.setSelected(True)
                    self.circuit_scene.rotate_selected_component(90.0)
                elif action == act_del:
                    top_item.setSelected(True)
                    self.circuit_scene.delete_selected_items()
                elif act_lock and action == act_lock:
                    self._open_lock_dialog(top_item.component_id, is_wire=False)
                event.accept()
                return
        super().contextMenuEvent(event)

    def _change_wire_color(self, wire, new_color: str):
        old_color = wire.color_str
        if old_color == new_color:
            return
        if hasattr(self.circuit_scene, "undo_stack") and self.circuit_scene.undo_stack:
            from .undo_commands import ChangeWireColorCommand
            cmd = ChangeWireColorCommand(self.circuit_scene, wire.connection_id, old_color, new_color)
            self.circuit_scene.undo_stack.push(cmd)
        else:
            conn = next((c for c in self.circuit_scene.connections if c.id == wire.connection_id), None)
            if conn:
                conn.color = new_color
            wire.color_str = new_color
            wire.update()

    def _open_lock_dialog(self, comp_id: str, is_wire: bool = False):
        from ..panels.education.lock_dialog import LockPropertiesDialog
        from esp32_lab.ui.main_window import MainWindow
        main_win = self.window()
        if not isinstance(main_win, MainWindow):
            return
            
        dialog = LockPropertiesDialog(comp_id, main_win.current_project, self.circuit_scene.interaction_policy, self)
        if dialog.exec() == 1:
            locks = dialog.get_locks()
            
            # Ensure pedagogy_profile exists
            if main_win.current_project.pedagogy_profile is None:
                main_win.current_project.pedagogy_profile = {"locked_elements": {"components": [], "wires": []}}
                
            locked_elems = main_win.current_project.pedagogy_profile.setdefault("locked_elements", {})
            lst = locked_elems.setdefault("wires" if is_wire else "components", [])
            
            # Update or insert
            found = False
            for c in lst:
                if c.get("id") == comp_id:
                    c["locks"] = locks
                    found = True
                    break
            if not found:
                lst.append({"id": comp_id, "locks": locks})
                
            # Reload policy and UI
            self.circuit_scene.interaction_policy.load_from_project(main_win.current_project)
            self.circuit_scene._update_all_interaction_flags()
            self.circuit_scene.update()
            main_win._is_manually_modified = True
