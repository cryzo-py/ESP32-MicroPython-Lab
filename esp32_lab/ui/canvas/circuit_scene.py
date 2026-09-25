"""
Scène graphique interactive (CircuitScene) gérant les composants, le câblage,
la platine d'expérimentation (Breadboard) et la simulation physique en temps réel.
"""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

from ...app.event_bus import get_event_bus
from ...application.education.interaction_policy import InteractionPolicy
from ...core.app_state import AppState
from ...core.models.connection import ConnectionModel
from ...simulator.modules.liquidcrystal_i2c import add_lcd_listener
from ...simulator.modules.neopixel import add_neopixel_listener
from .items.board_item import BoardGraphicsItem
from .items.breadboard_item import BreadboardGraphicsItem, BreadboardHoleItem
from .items.button_item import ButtonGraphicsItem
from .items.buzzer_item import BuzzerGraphicsItem
from .items.dht22_item import DHT22GraphicsItem
from .items.hcsr04_item import HCSR04GraphicsItem
from .items.joystick_item import JoystickGraphicsItem
from .items.lcd_item import LCDGraphicsItem
from .items.ldr_item import LDRGraphicsItem
from .items.led_item import LEDGraphicsItem
from .items.neopixel_item import NeoPixelGraphicsItem
from .items.oled_item import OLEDGraphicsItem
from .items.pin_item import PinAnchorItem
from .items.pir_item import PIRGraphicsItem
from .items.potentiometer_item import PotentiometerGraphicsItem
from .items.relay_item import RelayGraphicsItem
from .items.resistor_item import ResistorGraphicsItem
from .items.rgb_led_item import RGBLEDGraphicsItem
from .items.servo_item import ServoGraphicsItem
from .items.switch_item import SlideSwitchGraphicsItem
from .items.usb_cable_item import USBCableGraphicsItem
from .items.bme280_item import BME280GraphicsItem
from .items.mpu6050_item import MPU6050GraphicsItem
from .items.stepper_item import StepperMotorGraphicsItem
from .items.tm1637_item import TM1637GraphicsItem
from ...simulator.modules.tm1637 import add_tm1637_listener
from .wire_item import WireGraphicsItem
from ...core.breadboard_topology import BreadboardTopology
from ...core.electrical_net_resolver import ElectricalNetResolver
from .snap_engine import SnapEngine, SnapResult, extract_pins, PlacementPreview


class CircuitScene(QGraphicsScene):
    lcd_update_signal = Signal(list)
    neopixel_update_signal = Signal(int, list)
    tm1637_update_signal = Signal(str, bool)

    def __init__(self, parent=None, interaction_policy: InteractionPolicy = None):
        super().__init__(parent)
        self.setSceneRect(-200, -200, 1100, 850)
        self.setBackgroundBrush(QColor("#111827"))

        self.event_bus = get_event_bus()
        self.interaction_policy = interaction_policy or InteractionPolicy(AppState())
        self.interaction_policy._app_state.on_mode_changed(lambda mode: self._update_all_interaction_flags())
        self.board_item: BoardGraphicsItem | None = None
        self.breadboard_item: BreadboardGraphicsItem | None = None

        self.component_items: dict[str, BaseComponentItem] = {}
        self.device_models: dict[str, object] = {}
        self.wire_items: dict[str, WireGraphicsItem] = {}
        self.connections: list[ConnectionModel] = []
        
        self.topology = BreadboardTopology()
        self.snap_engine = SnapEngine()
        self.undo_stack = None
        self.is_modified: bool = False

        # État pour le câblage interactif
        self._pending_wire_start_pin: PinAnchorItem | None = None
        self._temp_wire: WireGraphicsItem | None = None

        self.theme_name = "dark"

        # Écoute des événements GPIO et PWM
        self.event_bus.gpio_changed.connect(self._on_gpio_changed)
        self.event_bus.pwm_changed.connect(self._on_pwm_changed)
        self.event_bus.simulation_stopped.connect(self._on_simulation_stopped)
        self.event_bus.display_updated.connect(self._handle_oled_update_gui)
        self.event_bus.component_property_changed.connect(self._on_component_property_changed)

        # Synchronisation thread-safe vers le thread UI
        self.lcd_update_signal.connect(self._handle_lcd_update_gui)
        self.neopixel_update_signal.connect(self._handle_neopixel_update_gui)
        self.tm1637_update_signal.connect(self._handle_tm1637_update_gui)

        add_lcd_listener(self._on_lcd_update)
        add_neopixel_listener(self._on_neopixel_update)
        add_tm1637_listener(self._on_tm1637_update)

        # Câble USB dynamique asservi au matériel réel
        self.usb_cable_item = USBCableGraphicsItem()
        self.addItem(self.usb_cable_item)
        self._is_usb_hardware_connected = False
        self.event_bus.usb_hardware_detected.connect(self._on_usb_hardware_detected)
        self.event_bus.device_connected.connect(lambda port: self._on_usb_hardware_detected(True, port))
        self.event_bus.device_disconnected.connect(lambda: self._on_usb_hardware_detected(False, ""))
        
        # Hooks pour Zombie States (Priority 2)
        self.event_bus.wire_added.connect(lambda w: self.re_evaluate_topology())
        self.event_bus.wire_removed.connect(lambda w_id: self.re_evaluate_topology())
        self.event_bus.connection_updated.connect(lambda w: self.re_evaluate_topology())
        self.event_bus.component_added.connect(lambda c: self.re_evaluate_topology())
        self.event_bus.component_removed.connect(lambda c: self.re_evaluate_topology())
        self.event_bus.component_moved.connect(lambda c,x,y: self.re_evaluate_topology())
        self.is_orthogonal_routing = False

    def set_orthogonal_routing(self, enabled: bool):
        """Active ou désactive le routage orthogonal (angles droits 90°) sur tous les fils."""
        self.is_orthogonal_routing = bool(enabled)
        for wire in self.wire_items.values():
            wire.set_orthogonal_mode(self.is_orthogonal_routing)
        self.update()

    def set_theme(self, theme_name: str = "dark"):
        """Applique la palette du thème (sombre ou clair) à la scène de circuit."""
        self.theme_name = theme_name
        if theme_name == "light":
            self.setBackgroundBrush(QColor("#f1f5f9"))
        else:
            self.setBackgroundBrush(QColor("#111827"))
        self.update()

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        dot_color = QColor("#cbd5e1") if getattr(self, "theme_name", "dark") == "light" else QColor("#1e293b")
        painter.setPen(QPen(dot_color, 1))
        grid_step = 20
        left = int(rect.left()) - (int(rect.left()) % grid_step)
        top = int(rect.top()) - (int(rect.top()) % grid_step)

        points = []
        for x in range(left, int(rect.right()), grid_step):
            for y in range(top, int(rect.bottom()), grid_step):
                points.append(QPointF(x, y))
        painter.drawPoints(points)

    def _update_all_interaction_flags(self):
        from PySide6.QtWidgets import QGraphicsItem
        for comp_id, item in self.component_items.items():
            if self.interaction_policy.can_move(comp_id):
                item.setFlag(QGraphicsItem.ItemIsMovable, True)
            else:
                item.setFlag(QGraphicsItem.ItemIsMovable, False)
        # Apply to wires as well
        for wire_id, wire in self.wire_items.items():
            # Actually wires might not be movable directly in the same way, but let's be safe
            pass

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        from esp32_lab.core.app_state import AppMode
        
        # Only show padlock in TEACHER mode
        if self.interaction_policy._app_state.mode == AppMode.TEACHER:
            from PySide6.QtGui import QPen, QColor, QFont
            from PySide6.QtCore import Qt, QRectF
            
            painter.setFont(QFont("Arial", 10))
            for comp_id, item in self.component_items.items():
                locks = self.interaction_policy._locks.get(comp_id)
                if locks and (locks.movement or locks.deletion or locks.rotation or locks.interaction or locks.properties):
                    bounds = item.sceneBoundingRect()
                    # Draw a small lock emoji or badge in top right
                    x = bounds.right() - 15
                    y = bounds.top() - 5
                    
                    # Background
                    painter.setBrush(QColor(239, 68, 68, 200)) # Red
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(x, y, 20, 20)
                    
                    # Text
                    painter.setPen(Qt.white)
                    painter.drawText(QRectF(x, y, 20, 20), Qt.AlignCenter, "🔒")

    def load_project_circuit(self, project):
        """Initialise ou réinitialise la scène avec les éléments du projet"""
        self.clear()
        self.component_items.clear()
        self.wire_items.clear()
        self.connections = list(project.connections)
        self.topology.clear()
        self.device_models.clear()
        self.interaction_policy.load_from_project(project)

        # 1. Carte ESP32 si présente dans le projet
        board_comp = next((c for c in project.components if c.type in ("esp32", "board")), None)
        if board_comp:
            self.board_item = BoardGraphicsItem(board_id="esp32")
            self.board_item.setPos(board_comp.x, board_comp.y)
            self.addItem(self.board_item)
            self.component_items["esp32"] = self.board_item
            self._connect_anchors(self.board_item)
        elif getattr(project, "board_id", None):
            # Projet avec board_id : instancier la carte ESP32
            self.board_item = BoardGraphicsItem(board_id="esp32")
            self.board_item.setPos(60, 60)
            self.addItem(self.board_item)
            self.component_items["esp32"] = self.board_item
            self._connect_anchors(self.board_item)
        else:
            self.board_item = None

        # Câble USB de liaison matérielle
        self.usb_cable_item = USBCableGraphicsItem()
        self.addItem(self.usb_cable_item)
        if self.board_item:
            self._update_usb_cable_pos()
            is_conn = getattr(self, "_is_usb_hardware_connected", False)
            self.usb_cable_item.set_connected(is_conn)
            self.board_item.set_powered(is_conn)

        # 2. Platine d'expérimentation (Breadboard) d'abord si présente
        bb_comp = next((c for c in project.components if c.type == "breadboard"), None)
        if bb_comp:
            item = BreadboardGraphicsItem(bb_comp.id)
            item.setPos(bb_comp.x, bb_comp.y)
            self.addItem(item)
            self.breadboard_item = item
            self.component_items[bb_comp.id] = item
            self._connect_anchors(item)
        else:
            self.breadboard_item = None

        # 3. Composants du projet
        for comp in project.components:
            if comp.type == "breadboard":
                continue

            item = self._create_component_item(comp.type, comp.id)
            if item:
                # Appliquer les propriétés spécifiques au composant restauré
                if comp.type == "led" and isinstance(item, LEDGraphicsItem):
                    item.color = comp.properties.get("color", "red")
                    item.update()
                elif comp.type == "resistor" and hasattr(item, "resistance_value"):
                    item.resistance_value = comp.properties.get("value", 220)
                elif comp.type == "potentiometer" and hasattr(item, "set_raw_value"):
                    item.set_raw_value(comp.properties.get("raw_value", 2048))
                elif comp.type == "servo" and hasattr(item, "set_angle"):
                    item.set_angle(comp.properties.get("angle", 90.0))
                elif comp.type == "dht22" and hasattr(item, "set_environment"):
                    item.set_environment(comp.properties.get("temperature", 24.5), comp.properties.get("humidity", 55.0))
                elif comp.type == "oled" and hasattr(item, "width"):
                    item.width = comp.properties.get("width", 128)
                    item.height = comp.properties.get("height", 64)
                elif comp.type == "hcsr04" and hasattr(item, "set_distance"):
                    item.set_distance(comp.properties.get("distance_cm", 25.0))
                elif comp.type in ("neopixel", "ws2812", "ws2812b") and hasattr(item, "num_leds"):
                    item.num_leds = comp.properties.get("num_leds", 8)
                elif comp.type in ("bme280", "bmp280") and hasattr(item, "set_environment"):
                    item.set_environment(comp.properties.get("temperature", 24.5), comp.properties.get("humidity", 50.0), comp.properties.get("pressure", 1013.25))
                elif comp.type in ("mpu6050", "mpu_6050", "gy521", "imu") and hasattr(item, "set_orientation"):
                    item.set_orientation(comp.properties.get("pitch", 0.0), comp.properties.get("roll", 0.0))
                elif comp.type in ("stepper", "stepper_motor", "28byj48", "uln2003") and hasattr(item, "set_current_angle"):
                    item.set_current_angle(comp.properties.get("angle", 0.0))
                elif comp.type in ("tm1637", "7segment", "display_7seg", "digit4") and hasattr(item, "set_text"):
                    item.set_text(comp.properties.get("text", "12:00"))

                target_scene_pos = QPointF(comp.x, comp.y)
                if self.breadboard_item and comp.pin_insertions:
                    # Restaurer les insertions depuis le modèle sauvegardé
                    item.setParentItem(self.breadboard_item)
                    item.setPos(self.breadboard_item.mapFromScene(target_scene_pos))
                    snap_result = SnapResult(
                        local_pos=self.breadboard_item.mapFromScene(target_scene_pos),
                        pin_to_hole=dict(comp.pin_insertions)
                    )
                    self._insert_component_in_breadboard(item, snap_result)
                elif self.breadboard_item and self.breadboard_item.contains_scene_pos(target_scene_pos):
                    # Tenter un snap automatique
                    pins = extract_pins(item)
                    local_pos = self.breadboard_item.mapFromScene(target_scene_pos)
                    snap = self.snap_engine.compute_snap(pins, local_pos, self.topology)
                    if snap:
                        item.setParentItem(self.breadboard_item)
                        item.setPos(snap.local_pos)
                        self._insert_component_in_breadboard(item, snap)
                    else:
                        item.setPos(target_scene_pos)
                        self.addItem(item)
                else:
                    item.setPos(target_scene_pos)
                    self.addItem(item)

                self.component_items[comp.id] = item
                self._connect_anchors(item)
                if getattr(comp, "rotation", 0.0):
                    item.setRotation(float(comp.rotation))

        # 4. Fils de connexion
        for conn in self.connections:
            self._create_wire_item(conn)
        self._update_all_interaction_flags()
        self.is_modified = False
        self.re_evaluate_topology()

    def _insert_component_in_breadboard(self, item, snap_result: SnapResult):
        """Enregistre chaque broche du composant dans un trou de la topologie et met à jour son état physique."""
        for pin_id, hole_id in snap_result.pin_to_hole.items():
            self.topology.insert_pin(item.component_id, pin_id, hole_id)
            hole = self.breadboard_item.hole_anchors.get(hole_id)
            if hole:
                hole.set_occupied(item.component_id, pin_id)

        # Mettre à jour la géométrie et l'occlusion des broches physiques du composant
        for child in item.childItems():
            if isinstance(child, PinAnchorItem) and child.pin_id in snap_result.pin_to_hole:
                hole_id = snap_result.pin_to_hole[child.pin_id]
                if hasattr(child, "set_inserted"):
                    child.set_inserted(hole_id, depth=8.0)

    def _remove_component_from_breadboard(self, item):
        """Retire toutes les broches du composant de la topologie et restaure leur longueur visible intégrale."""
        freed = self.topology.remove_component(item.component_id)
        if self.breadboard_item:
            for hole_id in freed:
                hole = self.breadboard_item.hole_anchors.get(hole_id)
                if hole:
                    hole.set_free()

        # Restaurer la géométrie libre de chaque broche physique
        for child in item.childItems():
            if hasattr(child, "set_removed"):
                child.set_removed()

    def preview_component_placement(
        self,
        component: QGraphicsItem,
        scene_pos: QPointF,
        rotation: float | None = None
    ) -> PlacementPreview:
        """Calcule l'état de prévisualisation (VALID_PREVIEW / INVALID_PREVIEW) sans modifier la topologie."""
        bb = self.breadboard_item
        rot = rotation if rotation is not None else component.rotation()
        if not bb or not bb.contains_scene_pos(scene_pos):
            return PlacementPreview(
                valid=False,
                target_holes=[],
                invalid_holes=[],
                pin_to_hole_map={},
                snap_position=scene_pos,
                rotation=rot,
                reason="OUT_OF_BREADBOARD"
            )

        pins = extract_pins(component, rotation=rot)
        local_pos = bb.mapFromScene(scene_pos)
        comp_id = getattr(component, "component_id", None)

        return self.snap_engine.compute_placement_preview(
            pins=pins,
            drop_local_pos=local_pos,
            topology=self.topology,
            rotation=rot,
            current_comp_id=comp_id
        )

    def commit_component_placement(self, component: QGraphicsItem, preview: PlacementPreview) -> bool:
        """Valide et applique l'insertion physique sur la breadboard selon les résultats du preview."""
        if not preview.valid or not self.breadboard_item:
            return False

        bb = self.breadboard_item
        if component.parentItem() != bb:
            component.setParentItem(bb)

        component.setPos(preview.snap_position)

        snap_res = SnapResult(local_pos=preview.snap_position, pin_to_hole=preview.pin_to_hole_map)
        self._insert_component_in_breadboard(component, snap_res)

        component._last_valid_pos = preview.snap_position
        component._last_valid_parent = bb
        component._last_valid_holes = dict(preview.pin_to_hole_map)
        component._last_valid_rotation = component.rotation()

        bb.clear_preview_highlights()
        self.update_all_wires()
        self.is_modified = True
        return True

    def reject_component_placement(self, component: QGraphicsItem, preview: PlacementPreview | None = None) -> None:
        """Rejette une tentative de placement invalide et restaure la position précédente sans corrompre la topologie."""
        bb = self.breadboard_item
        if bb and preview:
            bb.set_preview_states(valid_holes=[], invalid_holes=preview.invalid_holes or preview.target_holes)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1200, bb.clear_preview_highlights)

        if hasattr(component, "_last_valid_pos") and component._last_valid_pos is not None:
            if hasattr(component, "_last_valid_parent") and component._last_valid_parent:
                component.setParentItem(component._last_valid_parent)
            component.setPos(component._last_valid_pos)
            if hasattr(component, "_last_valid_rotation") and component._last_valid_rotation is not None:
                component.setRotation(component._last_valid_rotation)
            if hasattr(component, "_last_valid_holes") and component._last_valid_holes:
                snap_res = SnapResult(local_pos=component._last_valid_pos, pin_to_hole=component._last_valid_holes)
                self._insert_component_in_breadboard(component, snap_res)
        else:
            self._remove_component_from_breadboard(component)
            if bb and component.parentItem() == bb:
                sp = component.scenePos()
                component.setParentItem(None)
                if component.scene() != self:
                    self.addItem(component)
                component.setPos(sp)

        self.update_all_wires()

    def _create_component_item(self, base_type: str, comp_id: str):
        base = base_type.lower()
        if base in ("esp32", "board"):
            from esp32_lab.ui.canvas.items.board_item import BoardGraphicsItem
            return BoardGraphicsItem(board_id="esp32")
        elif base == "breadboard":
            return BreadboardGraphicsItem(comp_id)
        elif base == "led":
            from esp32_lab.simulator.devices.led import LEDModel
            self.device_models[comp_id] = LEDModel(comp_id)
            return LEDGraphicsItem(comp_id, color_name="red")
        elif base == "resistor":
            return ResistorGraphicsItem(comp_id, resistance_value=220)
        elif base == "button":
            from esp32_lab.simulator.devices.button import ButtonModel
            self.device_models[comp_id] = ButtonModel(comp_id)
            btn = ButtonGraphicsItem(comp_id)
            btn.button_pressed.connect(lambda cid=comp_id: self._on_button_pressed(cid))
            btn.button_released.connect(lambda cid=comp_id: self._on_button_released(cid))
            return btn
        elif base == "potentiometer":
            from esp32_lab.simulator.devices.potentiometer import PotentiometerModel
            self.device_models[comp_id] = PotentiometerModel(comp_id)
            pot = PotentiometerGraphicsItem(comp_id, raw_value=2048)
            pot.value_changed.connect(self._on_potentiometer_changed)
            return pot
        elif base == "servo":
            from esp32_lab.simulator.devices.servo import ServoModel
            self.device_models[comp_id] = ServoModel(comp_id)
            return ServoGraphicsItem(comp_id, angle=90.0)
        elif base == "buzzer":
            return BuzzerGraphicsItem(comp_id)
        elif base == "dht22":
            return DHT22GraphicsItem(comp_id)
        elif base == "oled":
            from esp32_lab.simulator.devices.ssd1306 import SSD1306Model
            self.device_models[comp_id] = SSD1306Model(comp_id)
            return OLEDGraphicsItem(comp_id)
        elif base == "hcsr04":
            return HCSR04GraphicsItem(comp_id)
        elif base in ("lcd", "lcd16x2"):
            return LCDGraphicsItem(comp_id)
        elif base == "relay":
            return RelayGraphicsItem(comp_id)
        elif base in ("neopixel", "ws2812", "ws2812b"):
            return NeoPixelGraphicsItem(comp_id, num_leds=8)
        elif base in ("ldr", "photoresistor", "light_sensor"):
            return LDRGraphicsItem(comp_id, lux=300.0)
        elif base in ("rgb_led", "rgbled", "led_rgb"):
            return RGBLEDGraphicsItem(comp_id, r=255, g=0, b=0)
        elif base in ("pir", "motion_sensor", "hcsr501"):
            return PIRGraphicsItem(comp_id)
        elif base in ("joystick", "thumbstick", "ky023"):
            return JoystickGraphicsItem(comp_id, x_val=2048, y_val=2048)
        elif base in ("switch", "slide_switch", "slideswitch"):
            return SlideSwitchGraphicsItem(comp_id, is_on=False)
        elif base in ("bme280", "bmp280"):
            from esp32_lab.simulator.devices.bme280 import BME280Model
            self.device_models[comp_id] = BME280Model(comp_id)
            return BME280GraphicsItem(comp_id)
        elif base in ("w25q", "w25q32", "w25q64"):
            from esp32_lab.simulator.devices.w25q import W25QxxModel
            from esp32_lab.ui.canvas.items.w25q_item import W25QItem
            variant = "W25Q64" if "64" in base else "W25Q32"
            self.device_models[comp_id] = W25QxxModel(comp_id, variant=variant)
            return W25QItem(comp_id, variant=variant)
        elif base in ("mpu6050", "mpu_6050", "gy521", "imu"):
            return MPU6050GraphicsItem(comp_id)
        elif base in ("stepper", "stepper_motor", "28byj48", "uln2003"):
            return StepperMotorGraphicsItem(comp_id)
        elif base in ("tm1637", "7segment", "display_7seg", "digit4"):
            return TM1637GraphicsItem(comp_id)
        elif base in ("uart_terminal", "uart", "terminal"):
            from esp32_lab.simulator.devices.uart_terminal import UARTTerminalModel
            from esp32_lab.ui.canvas.items.uart_terminal_item import UARTTerminalItem
            self.device_models[comp_id] = UARTTerminalModel(comp_id)
            return UARTTerminalItem(comp_id, scene=self)
        else:
            return LEDGraphicsItem(comp_id, color_name="red")

    def add_component(self, comp_type: str, pos: QPointF | None = None) -> QGraphicsItem:
        """Ajoute un nouveau composant sur la scene"""
        base = comp_type.lower()
        idx = 1
        while f"{base}_{idx}" in self.component_items:
            idx += 1
        comp_id = f"{base}_{idx}"

        item = self._create_component_item(base, comp_id)
        if base in ("esp32", "board"):
            self.board_item = item
        elif base == "breadboard":
            self.breadboard_item = item

        # Position par défaut si non spécifiée
        if pos is None:
            if self.breadboard_item and base != "breadboard":
                bb_pos = self.breadboard_item.pos()
                pos = QPointF(bb_pos.x() + 50, bb_pos.y() + 60 + (idx - 1) * 30)
            else:
                pos = QPointF(200, 150)

        # Magnétisme et insertion mécanique sur la platine d'expérimentation
        if self.breadboard_item and base != "breadboard":
            if self.breadboard_item.contains_scene_pos(pos):
                preview = self.preview_component_placement(item, pos)
                if preview.valid:
                    self.commit_component_placement(item, preview)
                else:
                    item.setPos(pos)
                    self.addItem(item)
            else:
                item.setPos(pos)
                self.addItem(item)
        else:
            item.setPos(pos)
            self.addItem(item)

        self.component_items[comp_id] = item
        self._connect_anchors(item)

        self.clearSelection()
        # Cache pour get_connected_pins
        self._last_resolver = None

        item.setSelected(True)
        self.event_bus.component_property_changed.emit(comp_id, {"added": True})
        self.update_all_wires()
        return item

    def _on_component_property_changed(self, comp_id: str, props: dict):
        item = self.component_items.get(comp_id)
        if item and type(item).__name__ == "LEDGraphicsItem":
            if "brightness" in props:
                item.set_brightness(props["brightness"])
        elif item and type(item).__name__ == "ServoGraphicsItem":
            if "angle" in props:
                item.set_angle(props["angle"])

    def _connect_anchors(self, item):
        """Attache l'événement de clic des ancres de broches"""
        for child in item.childItems():
            if isinstance(child, PinAnchorItem):
                child.pin_clicked.connect(self._on_pin_clicked)

    def _on_pin_clicked(self, pin: PinAnchorItem):
        """Gère le clic sur une broche pour créer ou terminer un fil"""
        if self._pending_wire_start_pin is None:
            self._pending_wire_start_pin = pin
            pin._is_active = True
            pin.update()
        else:
            start_pin = self._pending_wire_start_pin
            end_pin = pin

            if start_pin != end_pin:
                conn = ConnectionModel(
                    from_component=start_pin.owner_id,
                    from_pin=start_pin.pin_id,
                    to_component=end_pin.owner_id,
                    to_pin=end_pin.pin_id,
                    color="#38bdf8"
                )
                self.connections.append(conn)
                self._create_wire_item(conn)
                self.event_bus.wire_added.emit(conn)

                if isinstance(start_pin, BreadboardHoleItem):
                    start_pin.has_wire = True
                    start_pin.update()
                if isinstance(end_pin, BreadboardHoleItem):
                    end_pin.has_wire = True
                    end_pin.update()

                if self.undo_stack:
                    from .undo_commands import AddWireCommand
                    self.undo_stack.push(AddWireCommand(self, conn, initial_applied=True))

            start_pin._is_active = False
            start_pin.update()
            self._pending_wire_start_pin = None

    def _create_wire_item(self, conn: ConnectionModel):
        wire = WireGraphicsItem(conn.id, color=conn.color)
        wire.set_orthogonal_mode(getattr(self, "is_orthogonal_routing", False))
        self.addItem(wire)
        self.wire_items[conn.id] = wire

        p1 = self._find_pin_anchor(conn.from_component, conn.from_pin)
        p2 = self._find_pin_anchor(conn.to_component, conn.to_pin)
        if isinstance(p1, BreadboardHoleItem):
            p1.has_wire = True
        if isinstance(p2, BreadboardHoleItem):
            p2.has_wire = True
            p2.update()
        self._update_wire_geometry(conn.id)

    def find_pin_anchor_near_scene_pos(self, scene_pos: QPointF, max_dist: float = 16.0) -> PinAnchorItem | None:
        """Trouve l'ancre de broche ou le trou de breadboard le plus proche d'une coordonnée scène."""
        best_anchor = None
        best_dist_sq = max_dist * max_dist

        # 1. Vérifier la Breadboard d'abord
        if self.breadboard_item and self.breadboard_item.contains_scene_pos(scene_pos):
            nearest = self.breadboard_item.find_nearest_hole(scene_pos, max_dist=max_dist)
            if nearest:
                h_id = nearest[0]
                hole = self.breadboard_item.hole_anchors.get(h_id)
                if hole:
                    return hole

        # 2. Vérifier les broches de l'ESP32
        if self.board_item:
            for anchor in self.board_item.pin_anchors.values():
                c = anchor.get_scene_center()
                d_sq = (scene_pos.x() - c.x()) ** 2 + (scene_pos.y() - c.y()) ** 2
                if d_sq <= best_dist_sq:
                    best_dist_sq = d_sq
                    best_anchor = anchor

        # 3. Vérifier les broches des composants physiques
        for comp in self.component_items.values():
            if comp == self.breadboard_item or comp == self.board_item:
                continue
            for child in comp.childItems():
                if isinstance(child, PinAnchorItem):
                    c = child.get_scene_center()
                    d_sq = (scene_pos.x() - c.x()) ** 2 + (scene_pos.y() - c.y()) ** 2
                    if d_sq <= best_dist_sq:
                        best_dist_sq = d_sq
                        best_anchor = child

        return best_anchor

    def reconnect_wire_terminal(self, connection_id: str, terminal: str, new_comp_id: str, new_pin_id: str) -> bool:
        """Déplace librement l'une des extrémités d'un fil (terminal 'start' ou 'end') vers une nouvelle broche/alvéole."""
        conn = next((c for c in self.connections if c.id == connection_id), None)
        wire = self.wire_items.get(connection_id)
        if not conn or not wire:
            return False

        # Vérifier que la nouvelle ancre existe
        new_anchor = self._find_pin_anchor(new_comp_id, new_pin_id)
        if not new_anchor:
            return False

        # Libérer l'ancien trou breadboard s'il n'a plus d'autres fils
        old_comp = conn.from_component if terminal == "start" else conn.to_component
        old_pin = conn.from_pin if terminal == "start" else conn.to_pin
        old_anchor = self._find_pin_anchor(old_comp, old_pin)

        # Mettre à jour le modèle de connexion
        if terminal == "start":
            conn.from_component = new_comp_id
            conn.from_pin = new_pin_id
        else:
            conn.to_component = new_comp_id
            conn.to_pin = new_pin_id

        # Mettre à jour has_wire sur l'ancienne ancre
        if isinstance(old_anchor, BreadboardHoleItem):
            # Vérifier si un autre fil est connecté à ce trou
            has_other = any(
                (c.id != conn.id) and ((c.from_component == old_comp and c.from_pin == old_pin) or (c.to_component == old_comp and c.to_pin == old_pin))
                for c in self.connections
            )
            old_anchor.has_wire = has_other
            old_anchor.update()

        # Marquer la nouvelle ancre
        if isinstance(new_anchor, BreadboardHoleItem):
            new_anchor.has_wire = True
            new_anchor.update()

        # Réajuster les coordonnées du fil
        self._update_wire_geometry(connection_id)
        self.update_all_wires()
        self.event_bus.connection_updated.emit(conn) if hasattr(self.event_bus, "connection_updated") else None
        return True


    def _find_pin_anchor(self, component_id: str, pin_id: str) -> PinAnchorItem | None:
        try:
            if component_id == "esp32" and self.board_item:
                anchor = self.board_item.get_pin_anchor(pin_id)
                if anchor:
                    return anchor
                return self.board_item.pin_anchors.get(pin_id)

            if ("breadboard" in component_id or component_id.startswith("bb")) and self.breadboard_item:
                anchor = self.breadboard_item.get_pin_anchor(pin_id)
                if anchor:
                    return anchor

            comp_item = self.component_items.get(component_id)
            if comp_item:
                if hasattr(comp_item, "get_pin_anchor"):
                    anchor = comp_item.get_pin_anchor(pin_id)
                    if anchor:
                        return anchor
                for child in comp_item.childItems():
                    if isinstance(child, PinAnchorItem) and child.pin_id == pin_id:
                        return child
        except (RuntimeError, ReferenceError):
            return None
        return None

    def _update_wire_geometry(self, connection_id: str):
        try:
            conn = next((c for c in self.connections if c.id == connection_id), None)
            wire = self.wire_items.get(connection_id)
            if not conn or not wire:
                return

            p1 = self._find_pin_anchor(conn.from_component, conn.from_pin)
            p2 = self._find_pin_anchor(conn.to_component, conn.to_pin)

            if p1 and p2:
                start_is_bb = "breadboard" in str(conn.from_component).lower() or str(conn.from_component).lower().startswith("bb")
                end_is_bb = "breadboard" in str(conn.to_component).lower() or str(conn.to_component).lower().startswith("bb")
                wire.set_terminal_genders(
                    start_gender="male" if start_is_bb else "female",
                    end_gender="male" if end_is_bb else "female"
                )
                wire.set_endpoints(p1.get_scene_center(), p2.get_scene_center())
        except (RuntimeError, ReferenceError):
            pass

    def update_all_wires(self):
        # MIN-06: Réinitialiser l'état des trous/pins avant recalcul
        for comp in self.component_items.values():
            for child in comp.childItems():
                if hasattr(child, "has_wire"):
                    child.has_wire = False
                for gc in child.childItems():
                    if hasattr(gc, "has_wire"):
                        gc.has_wire = False

        try:
            for conn in list(self.connections):
                self._update_wire_geometry(conn.id)
        except (RuntimeError, ReferenceError):
            pass

    def rotate_selected_component(self, angle_deg: float = 90.0):
        for item in self.selectedItems():
            comp_id = getattr(item, "component_id", None)
            if not comp_id or comp_id in ("breadboard_1",) or comp_id.startswith("breadboard"):
                continue
            if hasattr(self, "interaction_policy") and not self.interaction_policy.can_rotate(comp_id):
                continue

            old_pos = item.pos()
            old_parent = item.parentItem()
            old_holes = dict(self.topology.get_component_holes(comp_id))
            old_rot = item.rotation()

            new_rot = (item.rotation() + angle_deg) % 360.0
            item.setRotation(new_rot)

            # Si le composant est inséré sur la breadboard, réévaluer le placement dans la nouvelle orientation
            bb = self.breadboard_item
            if bb and (item.parentItem() == bb or bb.contains_scene_pos(item.scenePos())):
                self._remove_component_from_breadboard(item)
                preview = self.preview_component_placement(item, item.scenePos(), new_rot)
                if preview.valid:
                    self.commit_component_placement(item, preview)
                else:
                    # Ne rentre pas dans la grille à cette orientation : reste libre
                    item._last_valid_holes = {}

            new_pos = item.pos()
            new_parent = item.parentItem()
            new_holes = dict(self.topology.get_component_holes(comp_id))

            if self.undo_stack:
                from .undo_commands import MoveComponentCommand
                cmd = MoveComponentCommand(
                    self,
                    comp_id,
                    old_pos,
                    new_pos,
                    old_parent,
                    new_parent,
                    old_holes,
                    new_holes,
                    old_rot,
                    new_rot,
                    description="Rotation composant",
                    initial_applied=True,
                )
                self.undo_stack.push(cmd)

            self.event_bus.component_property_changed.emit(comp_id, {"rotation": new_rot})
        self.update_all_wires()

    def delete_selected_items(self):
        items = []
        for item in self.selectedItems():
            comp_id = getattr(item, 'component_id', None)
            conn_id = getattr(item, 'connection_id', None)
            if comp_id and not self.interaction_policy.can_delete(comp_id):
                continue
            if conn_id and not self.interaction_policy.can_delete(conn_id):
                continue
            items.append(item)
            
        if not items:
            return
        if self.undo_stack:
            from .undo_commands import DeleteItemsCommand
            self.undo_stack.push(DeleteItemsCommand(self, items))
        else:
            self._execute_delete_items(items)

    def _execute_delete_items(self, items: list):
        for item in items:
            if isinstance(item, WireGraphicsItem):
                conn_id = item.connection_id
                self.removeItem(item)
                self.wire_items.pop(conn_id, None)
                self.connections = [c for c in self.connections if c.id != conn_id]
            elif hasattr(item, "component_id"):
                self._remove_component_from_breadboard(item)
                comp_id = item.component_id
                to_remove = [c for c in self.connections if c.from_component == comp_id or c.to_component == comp_id]
                for c in to_remove:
                    w = self.wire_items.pop(c.id, None)
                    if w:
                        self.removeItem(w)
                    if c in self.connections:
                        self.connections.remove(c)
                self.removeItem(item)
                self.component_items.pop(comp_id, None)
        self.update_all_wires()
        self.re_evaluate_topology()
        self.is_modified = True

    # =========================================================================
    # Résolveur de netlist électrique complet (Breadboard, Wires, Composants)
    # =========================================================================

    def _create_net_resolver(self) -> ElectricalNetResolver:
        """Instancie et configure le résolveur de netlist avec les connexions et composants actuels."""
        resolver = ElectricalNetResolver(self.topology)
        
        # 1. Fils physiques et cavaliers
        for conn in self.connections:
            resolver.add_connection(conn.from_component, conn.from_pin, conn.to_component, conn.to_pin)

        # 2. Continuité interne des composants passifs et commutateurs
        for comp_id, item in self.component_items.items():
            if isinstance(item, ResistorGraphicsItem):
                resolver.add_internal_bridge(comp_id, "pin1", "pin2")
            elif isinstance(item, ButtonGraphicsItem):
                resolver.add_internal_bridge(comp_id, "pin1", "pin2")
                resolver.add_internal_bridge(comp_id, "pin3", "pin4")
                model = self.device_models.get(comp_id)
                if model and getattr(model, "pressed", False):
                    resolver.add_internal_bridge(comp_id, "pin1", "pin3")
            elif isinstance(item, RelayGraphicsItem):
                if getattr(item, "is_active", False):
                    resolver.add_internal_bridge(comp_id, "com", "no")
                else:
                    resolver.add_internal_bridge(comp_id, "com", "nc")

        return resolver

    def get_electrical_graph(self) -> dict[tuple[str, str], set[tuple[str, str]]]:
        """Génère le graphe équipotentiel complet basé sur la topologie de la breadboard."""
        resolver = self._create_net_resolver()
        bb_id = self.breadboard_item.breadboard_id if self.breadboard_item else None
        return resolver.build_graph(bb_id)

    def get_connected_pins(self, start_comp: str, start_pin: str) -> set[tuple[str, str]]:
        """Parcours pour trouver l'ensemble des broches reliées au même potentiel."""
        resolver = self._create_net_resolver()
        bb_id = self.breadboard_item.breadboard_id if self.breadboard_item else None
        return resolver.get_connected_pins(start_comp, start_pin, bb_id)

    def inspect_pin(self, comp_id: str, pin_id: str) -> dict:
        """Inspecte une broche et retourne ses détails topologiques et son net équipotentiel."""
        resolver = self._create_net_resolver()
        bb_id = self.breadboard_item.breadboard_id if self.breadboard_item else None
        return resolver.inspect_pin(comp_id, pin_id, bb_id)

    def explain_path(self, c1: str, p1: str, c2: str, p2: str) -> list[str]:
        """Explique le cheminement physique et électrique continu reliant deux bornes."""
        resolver = self._create_net_resolver()
        bb_id = self.breadboard_item.breadboard_id if self.breadboard_item else None
        return resolver.explain_path(c1, p1, c2, p2, bb_id)


    # =========================================================================
    # Propagation des signaux de simulation
    # =========================================================================

    def _on_gpio_changed(self, pin_num: int, value: int):
        """Réaction en temps réel aux signaux GPIO émis par le simulateur"""
        if pin_num == 2 and self.board_item:
            self.board_item.set_gpio2_led(bool(value))

        gpio_key = f"GPIO{pin_num}"
        reachable = self.get_connected_pins("esp32", gpio_key)

        for comp_id, pin_name in reachable:
            item = self.component_items.get(comp_id)
            if isinstance(item, LEDGraphicsItem) and pin_name in ("anode", "+ (Anode)"):
                item.set_state(bool(value))
            elif isinstance(item, RelayGraphicsItem) and pin_name in ("in", "vcc"):
                item.set_state(bool(value))
            elif isinstance(item, StepperMotorGraphicsItem) and pin_name.startswith("in"):
                if value == 1:
                    try:
                        step_idx = int(pin_name.replace("in", "")) - 1
                        item.set_step(step_idx)
                    except Exception:
                        pass
            elif type(item).__name__ == "BuzzerGraphicsItem" and pin_name in ("+", "vcc", "signal"):
                item.set_active(bool(value), 1000 if value else 0)
            elif type(item).__name__ == "RGBLEDGraphicsItem":
                if pin_name == "r":
                    item.set_pwm("r", 1000, 1023 if value else 0)
                elif pin_name == "g":
                    item.set_pwm("g", 1000, 1023 if value else 0)
                elif pin_name == "b":
                    item.set_pwm("b", 1000, 1023 if value else 0)

    def _on_button_pressed(self, comp_id: str):
        """Actionnement physique du bouton poussoir"""
        btn = self.component_items.get(comp_id)
        if not isinstance(btn, ButtonGraphicsItem):
            return
        btn.is_pressed = True
        btn.update()
        
        # Mettre à jour le modèle Backend
        model = self.device_models.get(comp_id)
        if model:
            model.pressed = True
            self.re_evaluate_topology()

    def _on_button_released(self, comp_id: str):
        """Relâchement du bouton poussoir"""
        btn = self.component_items.get(comp_id)
        if not isinstance(btn, ButtonGraphicsItem):
            return
        btn.is_pressed = False
        btn.update()
        
        # Mettre à jour le modèle Backend
        model = self.device_models.get(comp_id)
        if model:
            model.pressed = False
            self.re_evaluate_topology()


    def _on_potentiometer_changed(self, component_id: str, raw_value: int):
        """Met à jour le modèle logique du potentiomètre et réévalue la topologie."""
        if component_id in self.device_models:
            self.device_models[component_id].position = raw_value / 4095.0
        # On ne pousse plus l'ADC directement dans le GPIOManager !
        # L'ADCManager viendra lire l'état au besoin via read().

    def _on_pwm_changed(self, pin_num: int, freq: int, duty: int):
        """Met à jour servomoteurs et buzzers connectés au signal PWM"""
        gpio_key = f"GPIO{pin_num}"
        reachable = self.get_connected_pins("esp32", gpio_key)

        for comp_id, pin_name in reachable:
            item = self.component_items.get(comp_id)
            if isinstance(item, ServoGraphicsItem) and pin_name == "sig":
                duty_norm = max(26, min(128, duty))
                angle = (duty_norm - 26) / (128 - 26) * 180.0
                item.set_angle(angle)
            elif isinstance(item, BuzzerGraphicsItem) and pin_name in ("pos", "pin1"):
                item.set_active(duty > 0, freq)

    def _handle_oled_update_gui(self, component_id: str, width: int, height: int, buffer: bytes):
        item = self.component_items.get(component_id)
        if item and isinstance(item, OLEDGraphicsItem):
            item.update_buffer(width, height, buffer)

    def _on_lcd_update(self, lines: list[str]):
        self.lcd_update_signal.emit(lines)

    def _handle_lcd_update_gui(self, lines: list[str]):
        for item in self.component_items.values():
            if isinstance(item, LCDGraphicsItem):
                item.set_lines(lines)

    def _on_neopixel_update(self, pin_num: int, colors: list[tuple[int, int, int]]):
        self.neopixel_update_signal.emit(pin_num, colors)

    def _handle_neopixel_update_gui(self, pin_num: int, colors: list[tuple[int, int, int]]):
        gpio_key = f"GPIO{pin_num}"
        reachable = self.get_connected_pins("esp32", gpio_key)
        updated = False

        for comp_id, pin_name in reachable:
            item = self.component_items.get(comp_id)
            if isinstance(item, NeoPixelGraphicsItem) and pin_name in ("din", "din_pin"):
                item.set_colors(colors)

    def re_evaluate_topology(self):
        """Réévalue l'état visuel de tous les composants selon la topologie actuelle."""
        # 1. Émettre la topologie au moteur de simulation
        resolver = self._create_net_resolver()
        try:
            from esp32_lab.app.event_bus import get_event_bus
            get_event_bus().topology_updated.emit(resolver, self.device_models)
        except Exception:
            pass
            
        from ...simulator.modules import machine as sim_machine
        if not sim_machine.Pin._gpio_manager:
            return
        # Eteindre tout
        self._on_simulation_stopped()
        # Rallumer selon l'état actuel des GPIO
        mgr = sim_machine.Pin._gpio_manager
        for pin_num, value in list(mgr._values.items()):
            if value:
                self._on_gpio_changed(pin_num, value)

    def _on_simulation_stopped(self):
        if self.board_item:
            self.board_item.set_gpio2_led(False)
        for item in self.component_items.values():
            if isinstance(item, LEDGraphicsItem):
                item.set_state(False)
            elif isinstance(item, RelayGraphicsItem):
                item.set_state(False)
            elif isinstance(item, NeoPixelGraphicsItem):
                item.clear()
            elif isinstance(item, BuzzerGraphicsItem):
                item.set_active(False, 0)

    def _on_tm1637_update(self, text: str, colon: bool):
        self.tm1637_update_signal.emit(text, colon)

    def _handle_tm1637_update_gui(self, text: str, colon: bool):
        for item in self.component_items.values():
            if isinstance(item, TM1637GraphicsItem):
                item.set_display(text, colon)

    def _on_usb_hardware_detected(self, is_connected: bool, port_name: str = ""):
        self._is_usb_hardware_connected = bool(is_connected)
        if hasattr(self, "usb_cable_item") and self.usb_cable_item:
            self._update_usb_cable_pos()
            self.usb_cable_item.set_connected(self._is_usb_hardware_connected)
        if self.board_item:
            self.board_item.set_powered(self._is_usb_hardware_connected)

    def _update_usb_cable_pos(self):
        if self.board_item and hasattr(self, "usb_cable_item") and self.usb_cable_item:
            p = self.board_item.get_usb_socket_scene_pos()
            self.usb_cable_item.setPos(p)



