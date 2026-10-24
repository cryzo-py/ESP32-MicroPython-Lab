"""
Commandes modulaires pour l'historique Annuler / Rétablir (Undo / Redo - Ctrl+Z / Ctrl+Y)
"""

from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoCommand
from ...core.models.connection import ConnectionModel
from .snap_engine import SnapResult


class MoveComponentCommand(QUndoCommand):
    """Commande d'historique pour le déplacement d'un composant physique."""

    def __init__(
        self,
        scene,
        component_id: str,
        old_pos: QPointF,
        new_pos: QPointF,
        old_parent,
        new_parent,
        old_holes: dict[str, str],
        new_holes: dict[str, str],
        old_rotation: float,
        new_rotation: float,
        description: str = "Déplacement composant",
        initial_applied: bool = True,
    ):
        super().__init__(description)
        self.scene = scene
        self.component_id = component_id
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.old_parent = old_parent
        self.new_parent = new_parent
        self.old_holes = dict(old_holes or {})
        self.new_holes = dict(new_holes or {})
        self.old_rotation = old_rotation
        self.new_rotation = new_rotation
        self._initial_applied = initial_applied

    def redo(self):
        if self._initial_applied:
            self._initial_applied = False
            return

        item = self.scene.component_items.get(self.component_id)
        if not item:
            return

        bb = self.scene.breadboard_item
        self.scene._remove_component_from_breadboard(item)
        item.setParentItem(self.new_parent)
        item.setPos(self.new_pos)
        item.setRotation(self.new_rotation)

        if self.new_parent == bb and self.new_holes and bb:
            snap_res = SnapResult(local_pos=self.new_pos, pin_to_hole=self.new_holes)
            self.scene._insert_component_in_breadboard(item, snap_res)
            item._last_valid_pos = self.new_pos
            item._last_valid_parent = bb
            item._last_valid_holes = dict(self.new_holes)
        else:
            item._last_valid_pos = item.scenePos()
            item._last_valid_parent = None
            item._last_valid_holes = {}

        self.scene.update_all_wires()

    def undo(self):
        self._initial_applied = False
        item = self.scene.component_items.get(self.component_id)
        if not item:
            return

        bb = self.scene.breadboard_item
        self.scene._remove_component_from_breadboard(item)
        item.setParentItem(self.old_parent)
        item.setPos(self.old_pos)
        item.setRotation(self.old_rotation)

        if self.old_parent == bb and self.old_holes and bb:
            snap_res = SnapResult(local_pos=self.old_pos, pin_to_hole=self.old_holes)
            self.scene._insert_component_in_breadboard(item, snap_res)
            item._last_valid_pos = self.old_pos
            item._last_valid_parent = bb
            item._last_valid_holes = dict(self.old_holes)
        else:
            item._last_valid_pos = item.scenePos()
            item._last_valid_parent = None
            item._last_valid_holes = {}

        self.scene.update_all_wires()


class AddComponentCommand(QUndoCommand):
    """Commande d'historique pour l'ajout d'un composant."""

    def __init__(self, main_window, comp_type: str, description: str = "Ajout composant"):
        super().__init__(description)
        self.main_window = main_window
        self.comp_type = comp_type
        self.comp_model = None

    def redo(self):
        from ...core.models.component import ComponentModel
        if self.comp_model is None:
            self.comp_model = ComponentModel(
                type=self.comp_type,
                name=self.comp_type.capitalize(),
                x=350,
                y=200,
                properties={"color": "red" if self.comp_type == "led" else None}
            )
        if self.comp_model not in self.main_window.current_project.components:
            self.main_window.current_project.components.append(self.comp_model)
        self.main_window.circuit_scene.load_project_circuit(self.main_window.current_project)
        self.main_window.schematic_scene.load_project_schematic(self.main_window.current_project)
        if hasattr(self.main_window, "status_bar") and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"Composant '{self.comp_type}' ajouté à la platine.", 3000)

    def undo(self):
        if self.comp_model in self.main_window.current_project.components:
            self.main_window.current_project.components.remove(self.comp_model)
        self.main_window.circuit_scene.load_project_circuit(self.main_window.current_project)
        self.main_window.schematic_scene.load_project_schematic(self.main_window.current_project)
        if hasattr(self.main_window, "status_bar") and self.main_window.status_bar:
            self.main_window.status_bar.showMessage(f"Ajout du composant '{self.comp_type}' annulé.", 3000)


class DeleteItemsCommand(QUndoCommand):
    """Commande d'historique pour la suppression d'éléments (composants et fils)."""

    def __init__(self, scene, items_to_delete: list, description: str = "Suppression éléments"):
        super().__init__(description)
        self.scene = scene
        self.items_data = []
        self.wires_data = []

        # Développer la liste pour inclure les composants insérés sur une plaque breadboard supprimée
        expanded_items = list(items_to_delete)
        for it in items_to_delete:
            if hasattr(it, "component_id") and (it == getattr(scene, "breadboard_item", None) or str(getattr(it, "component_id", "")).startswith("breadboard")):
                for child in it.childItems():
                    child_cid = getattr(child, "component_id", None)
                    if child_cid and child_cid in scene.component_items and child not in expanded_items:
                        expanded_items.append(child)

        views = self.scene.views()
        main_win = views[0].window() if views else None

        for it in expanded_items:
            from .wire_item import WireGraphicsItem
            if isinstance(it, WireGraphicsItem):
                conn = next((c for c in scene.connections if c.id == it.connection_id), None)
                if conn and not any(w.id == conn.id for w in self.wires_data):
                    self.wires_data.append(ConnectionModel(
                        id=conn.id,
                        from_component=conn.from_component,
                        from_pin=conn.from_pin,
                        to_component=conn.to_component,
                        to_pin=conn.to_pin,
                        color=conn.color
                    ))
            elif hasattr(it, "component_id") or it == scene.board_item or it == scene.breadboard_item:
                cid = getattr(it, "component_id", None)
                if not cid:
                    if it == scene.board_item:
                        cid = getattr(scene.board_item, "board_id", "esp32")
                    elif it == scene.breadboard_item:
                        cid = getattr(scene.breadboard_item, "breadboard_id", "breadboard_1")

                if not cid:
                    continue

                # Respecter la politique de verrouillage pédagogique si applicable
                if hasattr(scene, "interaction_policy") and not scene.interaction_policy.can_delete(cid):
                    continue

                aliases = {cid}
                if cid in ("esp32", "board"):
                    aliases.update({"esp32", "board"})
                elif cid in ("arduino_uno", "uno"):
                    aliases.update({"arduino_uno", "uno"})

                for c in scene.connections:
                    if (c.from_component in aliases or c.to_component in aliases) and not any(w.id == c.id for w in self.wires_data):
                        self.wires_data.append(ConnectionModel(
                            id=c.id,
                            from_component=c.from_component,
                            from_pin=c.from_pin,
                            to_component=c.to_component,
                            to_pin=c.to_pin,
                            color=c.color
                        ))
                c_model = None
                if main_win and hasattr(main_win, "current_project") and main_win.current_project:
                    c_model = next((c for c in main_win.current_project.components if c.id == cid), None)

                self.items_data.append({
                    "item": it,
                    "cid": cid,
                    "pos": it.pos(),
                    "parent": it.parentItem(),
                    "holes": dict(getattr(it, "_last_valid_holes", {})),
                    "rotation": it.rotation(),
                    "model": c_model,
                })

    def redo(self):
        for w_data in self.wires_data:
            conn = next((c for c in self.scene.connections if c.id == w_data.id), None)
            wire_item = self.scene.wire_items.pop(w_data.id, None)
            if wire_item:
                self.scene.removeItem(wire_item)
            if conn and conn in self.scene.connections:
                self.scene.connections.remove(conn)

        # Retirer les composants insérés d'abord, puis la breadboard si présente
        bb_item = getattr(self.scene, "breadboard_item", None)
        ordered_comps = [c for c in self.items_data if c["item"] != bb_item and not str(c.get("cid", "")).startswith("breadboard")] + \
                        [c for c in self.items_data if c["item"] == bb_item or str(c.get("cid", "")).startswith("breadboard")]

        views = self.scene.views()
        main_win = views[0].window() if views else None

        for comp_dict in ordered_comps:
            it = comp_dict["item"]
            cid = comp_dict["cid"]
            self.scene._remove_component_from_breadboard(it)
            if it.scene() == self.scene:
                self.scene.removeItem(it)
            self.scene.component_items.pop(cid, None)
            if cid in ("esp32", "board"):
                self.scene.component_items.pop("esp32", None)
                self.scene.component_items.pop("board", None)
            elif cid in ("arduino_uno", "uno"):
                self.scene.component_items.pop("arduino_uno", None)
                self.scene.component_items.pop("uno", None)

            if it == getattr(self.scene, "board_item", None) or cid in ("esp32", "board", "arduino_uno", "uno"):
                self.scene.board_item = None
                if hasattr(self.scene, "usb_cable_item") and self.scene.usb_cable_item:
                    self.scene.usb_cable_item.set_connected(False)
                    self.scene.usb_cable_item.setVisible(False)
            if it == getattr(self.scene, "breadboard_item", None) or str(cid).startswith("breadboard"):
                self.scene.breadboard_item = None

            # Retirer du modèle de projet
            if main_win and hasattr(main_win, "current_project") and main_win.current_project:
                for c in list(main_win.current_project.components):
                    if c.id == cid or (cid in ("esp32", "board", "arduino_uno", "uno") and c.type in ("esp32", "board", "arduino_uno", "uno")):
                        main_win.current_project.components.remove(c)

        # Retirer les connexions du modèle
        if main_win and hasattr(main_win, "current_project") and main_win.current_project:
            main_win.current_project.connections = list(self.scene.connections)

        self.scene.update_all_wires()
        if hasattr(self.scene, "re_evaluate_topology"):
            self.scene.re_evaluate_topology()

    def undo(self):
        # 1. Restaurer la breadboard d'abord si elle faisait partie des éléments supprimés
        bb_comp_dict = next((c for c in self.items_data if c["cid"].startswith("breadboard") or hasattr(c["item"], "breadboard_id")), None)
        if bb_comp_dict:
            bb_it = bb_comp_dict["item"]
            self.scene.addItem(bb_it)
            bb_it.setPos(bb_comp_dict["pos"])
            bb_it.setRotation(bb_comp_dict["rotation"])
            self.scene.breadboard_item = bb_it
            self.scene.component_items[bb_comp_dict["cid"]] = bb_it

        bb = self.scene.breadboard_item

        # 2. Restaurer tous les autres composants
        for comp_dict in self.items_data:
            it = comp_dict["item"]
            cid = comp_dict["cid"]
            if it == bb:
                continue
            parent = comp_dict["parent"]
            if parent == bb and bb:
                it.setParentItem(bb)
            else:
                self.scene.addItem(it)
            it.setPos(comp_dict["pos"])
            it.setRotation(comp_dict["rotation"])
            self.scene.component_items[cid] = it
            if cid in ("esp32", "board"):
                self.scene.component_items["esp32"] = it
            elif cid in ("arduino_uno", "uno"):
                self.scene.component_items["arduino_uno"] = it

            if parent == bb and comp_dict["holes"] and bb:
                snap_res = SnapResult(local_pos=comp_dict["pos"], pin_to_hole=comp_dict["holes"])
                self.scene._insert_component_in_breadboard(it, snap_res)

            # Restaurer board_item si c'est la carte microcontrôleur
            from .items.board_item import BoardGraphicsItem
            from .items.arduino_uno_item import ArduinoUnoGraphicsItem
            if isinstance(it, (BoardGraphicsItem, ArduinoUnoGraphicsItem)) or cid in ("esp32", "board", "arduino_uno", "uno"):
                self.scene.board_item = it
                if hasattr(self.scene, "usb_cable_item") and self.scene.usb_cable_item:
                    self.scene._update_usb_cable_pos()
                    is_conn = getattr(self.scene, "_is_usb_hardware_connected", False)
                    self.scene.usb_cable_item.set_connected(is_conn)
                    self.scene.board_item.set_powered(is_conn)

        # 3. Restaurer les fils
        for w_data in self.wires_data:
            conn = ConnectionModel(
                id=w_data.id,
                from_component=w_data.from_component,
                from_pin=w_data.from_pin,
                to_component=w_data.to_component,
                to_pin=w_data.to_pin,
                color=w_data.color,
            )
            self.scene.connections.append(conn)
            self.scene._create_wire_item(conn)

        self.scene.update_all_wires()
        if hasattr(self.scene, "re_evaluate_topology"):
            self.scene.re_evaluate_topology()

        # 4. Remettre dans le modèle de projet
        views = self.scene.views()
        main_win = views[0].window() if views else None
        if main_win and hasattr(main_win, "current_project") and main_win.current_project:
            from ...core.models.component import ComponentModel
            for comp_dict in self.items_data:
                it = comp_dict["item"]
                cid = comp_dict["cid"]
                c_model = comp_dict.get("model")
                if not c_model:
                    c_type = getattr(it, "_comp_type", "unknown")
                    c_model = ComponentModel(id=cid, type=c_type, name="Restored", x=it.scenePos().x(), y=it.scenePos().y())
                if c_model not in main_win.current_project.components:
                    main_win.current_project.components.append(c_model)
            main_win.current_project.connections = list(self.scene.connections)


class MoveWireTerminalCommand(QUndoCommand):
    """Commande d'historique pour le déplacement d'une extrémité de fil."""

    def __init__(
        self,
        scene,
        connection_id: str,
        terminal: str,
        old_comp_id: str,
        old_pin_id: str,
        new_comp_id: str,
        new_pin_id: str,
        description: str = "Déplacement extrémité fil",
        initial_applied: bool = True,
    ):
        super().__init__(description)
        self.scene = scene
        self.connection_id = connection_id
        self.terminal = terminal
        self.old_comp_id = old_comp_id
        self.old_pin_id = old_pin_id
        self.new_comp_id = new_comp_id
        self.new_pin_id = new_pin_id
        self._initial_applied = initial_applied

    def redo(self):
        if self._initial_applied:
            self._initial_applied = False
            return
        self.scene.reconnect_wire_terminal(
            self.connection_id, self.terminal, self.new_comp_id, self.new_pin_id
        )

    def undo(self):
        self._initial_applied = False
        self.scene.reconnect_wire_terminal(
            self.connection_id, self.terminal, self.old_comp_id, self.old_pin_id
        )


class AddWireCommand(QUndoCommand):
    """Commande d'historique pour l'ajout d'un nouveau fil."""

    def __init__(self, scene, connection: ConnectionModel, description: str = "Ajout fil", initial_applied: bool = True):
        super().__init__(description)
        self.scene = scene
        self.conn = connection
        self._initial_applied = initial_applied

    def redo(self):
        if self._initial_applied:
            self._initial_applied = False
            return
        if self.conn not in self.scene.connections:
            self.scene.connections.append(self.conn)
        self.scene._create_wire_item(self.conn)
        self.scene.update_all_wires()

    def undo(self):
        self._initial_applied = False
        wire_item = self.scene.wire_items.pop(self.conn.id, None)
        if wire_item:
            self.scene.removeItem(wire_item)
        if self.conn in self.scene.connections:
            self.scene.connections.remove(self.conn)

        for cid, pid in [(self.conn.from_component, self.conn.from_pin), (self.conn.to_component, self.conn.to_pin)]:
            anchor = self.scene._find_pin_anchor(cid, pid)
            if anchor and hasattr(anchor, "has_wire"):
                still = any(
                    (c.from_component == cid and c.from_pin == pid) or
                    (c.to_component == cid and c.to_pin == pid)
                    for c in self.scene.connections
                )
                anchor.has_wire = still
                anchor.update()

        self.scene.update_all_wires()


class ChangeWireColorCommand(QUndoCommand):
    """Commande d'historique pour le changement de couleur d'un fil."""

    def __init__(self, scene, connection_id: str, old_color: str, new_color: str, description: str = "Couleur du fil"):
        super().__init__(description)
        self.scene = scene
        self.connection_id = connection_id
        self.old_color = old_color
        self.new_color = new_color

    def redo(self):
        self._apply_color(self.new_color)

    def undo(self):
        self._apply_color(self.old_color)

    def _apply_color(self, color: str):
        conn = next((c for c in self.scene.connections if c.id == self.connection_id), None)
        if conn:
            conn.color = color
        wire = self.scene.wire_items.get(self.connection_id)
        if wire:
            wire.color_str = color
            wire.update()

