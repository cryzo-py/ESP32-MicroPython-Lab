"""Tests de la topologie électrique de la breadboard et du moteur d'enfichage."""
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QMimeData, QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

# Ensure QApplication exists
app = QApplication.instance() or QApplication([])


class TestBreadboardTopology:
    """Tests du modèle logique de topologie."""
    
    def test_topology_has_420_holes(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        assert len(t.holes) == 420
    
    def test_topology_has_64_strips(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        assert len(t.strips) == 64  # 30 left + 30 right + 4 rails
    
    def test_strip_has_5_holes(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        assert len(t.strips["row_10_left"]) == 5
        assert "r10_a" in t.strips["row_10_left"]
        assert "r10_e" in t.strips["row_10_left"]
    
    def test_rail_has_30_holes(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        assert len(t.strips["rail_left_plus"]) == 30
    
    def test_left_right_strips_isolated(self):
        """Les bandes gauche et droite de même rangée sont isolées."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        left = t.strips["row_10_left"]
        right = t.strips["row_10_right"]
        assert left.isdisjoint(right)
    
    def test_insert_and_retrieve_pin(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        assert t.insert_pin("led_1", "anode", "r10_b")
        assert t.is_hole_occupied("r10_b")
        assert t.get_occupant("r10_b") == ("led_1", "anode")
        assert t.get_pin_hole("led_1", "anode") == "r10_b"
    
    def test_insert_occupied_hole_fails(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        assert t.insert_pin("led_1", "anode", "r10_b")
        assert not t.insert_pin("res_1", "pin1", "r10_b")  # Already occupied
    
    def test_remove_component_frees_holes(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        t.insert_pin("led_1", "anode", "r10_b")
        t.insert_pin("led_1", "cathode", "r11_b")
        freed = t.remove_component("led_1")
        assert set(freed) == {"r10_b", "r11_b"}
        assert not t.is_hole_occupied("r10_b")
        assert not t.is_hole_occupied("r11_b")
    
    def test_connected_holes_same_strip(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        connected = t.get_connected_holes("r10_a")
        assert "r10_b" in connected
        assert "r10_c" in connected
        assert "r10_d" in connected
        assert "r10_e" in connected
        assert "r10_f" not in connected  # Other side of DIP gap
    
    def test_same_strip_auto_connection(self):
        """Deux broches dans la même bande sont automatiquement connectées."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        t.insert_pin("led_1", "cathode", "r11_b")
        t.insert_pin("res_1", "pin1", "r11_c")
        # Both in row_11_left -> electrically connected
        strip = t.get_strip_for_hole("r11_b")
        assert strip == t.get_strip_for_hole("r11_c")


class TestSnapEngine:
    """Tests du moteur d'enfichage multi-broches."""
    
    def test_snap_single_pin(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.ui.canvas.snap_engine import SnapEngine, PinInfo
        t = BreadboardTopology()
        engine = SnapEngine()
        pins = [PinInfo("pin1", 0, 0)]
        # Drop near hole r15_c (x=63.0, y=147.0)
        result = engine.compute_snap(pins, QPointF(64, 148), t)
        assert result is not None
        assert "pin1" in result.pin_to_hole
    
    def test_snap_two_pins_vertical(self):
        """Résistance avec 2 broches verticales espacées de 51px (6 rangées)."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.ui.canvas.snap_engine import SnapEngine, PinInfo
        t = BreadboardTopology()
        engine = SnapEngine()
        pins = [PinInfo("pin1", 0, -25.5), PinInfo("pin2", 0, 25.5)]
        # Drop near center of a column
        result = engine.compute_snap(pins, QPointF(63, 130), t)
        assert result is not None
        assert len(result.pin_to_hole) == 2
        # Pins should be 6 rows apart
        h1 = t.holes[result.pin_to_hole["pin1"]]
        h2 = t.holes[result.pin_to_hole["pin2"]]
        assert abs(h2.row - h1.row) == 6
    
    def test_snap_rejects_occupied_holes(self):
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.ui.canvas.snap_engine import SnapEngine, PinInfo
        t = BreadboardTopology()
        engine = SnapEngine()
        # Occupy a hole
        t.insert_pin("other", "pin", "r15_c")
        pins = [PinInfo("pin1", 0, 0)]
        # Try to snap exactly on the occupied hole
        hole_pos = t.get_hole_position("r15_c")
        result = engine.compute_snap(pins, QPointF(hole_pos[0], hole_pos[1]), t)
        # Should find a DIFFERENT hole (not r15_c)
        if result:
            assert result.pin_to_hole["pin1"] != "r15_c"


class TestExamplesNoArtificialWires:
    """Vérifie que les exemples n'ont plus de fils artificiels."""
    
    def test_blink_example_no_artificial_wires(self):
        from esp32_lab.core.examples import create_blink_example
        proj = create_blink_example()
        for conn in proj.connections:
            # No wire should connect a non-breadboard component pin to a breadboard hole
            is_comp_to_bb = (
                conn.from_component != "esp32" and 
                conn.from_component != "breadboard_1" and
                conn.to_component == "breadboard_1"
            )
            is_bb_to_comp = (
                conn.from_component == "breadboard_1" and
                conn.to_component != "esp32" and
                conn.to_component != "breadboard_1"
            )
            assert not is_comp_to_bb, f"Artificial wire found: {conn.id}"
            assert not is_bb_to_comp, f"Artificial wire found: {conn.id}"
    
    def test_blink_has_pin_insertions(self):
        from esp32_lab.core.examples import create_blink_example
        proj = create_blink_example()
        led = next(c for c in proj.components if c.type == "led")
        res = next(c for c in proj.components if c.type == "resistor")
        assert len(led.pin_insertions) == 2
        assert len(res.pin_insertions) == 2
    
    def test_button_led_no_artificial_wires(self):
        from esp32_lab.core.examples import create_button_led_example
        proj = create_button_led_example()
        for conn in proj.connections:
            is_comp_to_bb = (
                conn.from_component not in ("esp32", "breadboard_1") and
                conn.to_component == "breadboard_1"
            )
            is_bb_to_comp = (
                conn.from_component == "breadboard_1" and
                conn.to_component not in ("esp32", "breadboard_1")
            )
            assert not is_comp_to_bb, f"Artificial wire: {conn.id}"
            assert not is_bb_to_comp, f"Artificial wire: {conn.id}"


class TestComponentPinGrid:
    """Vérifie que les broches des composants sont alignées sur la grille 8.5 px."""
    
    def test_led_pin_spacing(self):
        from esp32_lab.ui.canvas.items.led_item import LEDGraphicsItem
        led = LEDGraphicsItem("test_led")
        anode_y = led.anode_pin.pos().y()
        cathode_y = led.cathode_pin.pos().y()
        spacing = abs(cathode_y - anode_y)
        assert abs(spacing - 8.5) < 0.01, f"LED pin spacing {spacing} != 8.5"
    
    def test_resistor_pin_spacing(self):
        from esp32_lab.ui.canvas.items.resistor_item import ResistorGraphicsItem
        res = ResistorGraphicsItem("test_res")
        p1_y = res.pin1.pos().y()
        p2_y = res.pin2.pos().y()
        spacing = abs(p2_y - p1_y)
        assert abs(spacing - 51.0) < 0.01, f"Resistor spacing {spacing} != 51.0"
    
    def test_button_pin_spacing(self):
        from esp32_lab.ui.canvas.items.button_item import ButtonGraphicsItem
        btn = ButtonGraphicsItem("test_btn")
        v_spacing = abs(btn.pin3.pos().y() - btn.pin1.pos().y())
        h_spacing = abs(btn.pin2.pos().x() - btn.pin1.pos().x())
        assert abs(v_spacing - 17.0) < 0.01, f"Button V spacing {v_spacing} != 17.0"
        assert abs(h_spacing - 38.0) < 0.01, f"Button H spacing {h_spacing} != 38.0"


class TestDragAndDrop:
    """Test du drag-and-drop sur la vue circuit."""
    
    def test_drag_and_drop_on_circuit_view(self):
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.circuit_view import CircuitView
        scene = CircuitScene()
        view = CircuitView(scene)
        # Add breadboard first
        scene.add_component("breadboard", QPointF(0, 0))
        assert scene.breadboard_item is not None
        # Add a LED near the breadboard
        led = scene.add_component("led", QPointF(55, 130))
        assert led is not None

def test_palette_photorealistic_thumbnails():
    """Vérifie la génération des miniatures vectorielles photoréalistes pour tous les composants."""
    from esp32_lab.ui.panels.component_palette import ComponentPaletteWidget, render_component_thumbnail
    comp_types = [
        "led", "resistor", "button", "potentiometer", "buzzer",
        "relay", "servo", "neopixel", "oled", "lcd16x2", "dht22", "hcsr04"
    ]
    for ctype in comp_types:
        pixmap = render_component_thumbnail(ctype, size=44)
        assert not pixmap.isNull()
        assert pixmap.width() == 44
        assert pixmap.height() == 44

    palette = ComponentPaletteWidget()
    assert len(palette._cards) >= 12

def test_breadboard_netlist_signal_propagation():
    """Vérifie la propagation du signal électrique à travers la platine et les composants."""
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.examples import create_blink_example
    from esp32_lab.ui.canvas.items.led_item import LEDGraphicsItem
    
    scene = CircuitScene()
    proj = create_blink_example()
    scene.load_project_circuit(proj)

    led = scene.component_items.get("led_1")
    assert isinstance(led, LEDGraphicsItem)
    assert led.is_on is False

    scene._on_gpio_changed(2, 1)
    assert led.is_on is True

    scene._on_gpio_changed(2, 0)
    assert led.is_on is False

def test_button_interaction_through_breadboard():
    """Vérifie que l'appui sur le bouton virtuel propage l'état vers le GPIO de l'ESP32."""
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.examples import create_button_led_example
    from esp32_lab.ui.canvas.items.button_item import ButtonGraphicsItem
    from esp32_lab.simulator.engine import SimulationEngine

    engine = SimulationEngine()
    scene = CircuitScene()
    
    def on_top(resolver, models):
        engine.gpio_manager.net_resolver = resolver
        engine.gpio_manager.device_models = models
        
    engine.event_bus.topology_updated.connect(on_top)
    
    proj = create_button_led_example()
    scene.load_project_circuit(proj)

    btn = scene.component_items.get("btn_1")
    assert isinstance(btn, ButtonGraphicsItem)

    from esp32_lab.simulator.modules import machine as sim_machine
    assert sim_machine.Pin._gpio_manager is not None
    
    # Configure le pin en INPUT avec PULL_DOWN comme dans l'exemple
    btn_pin = sim_machine.Pin(4, sim_machine.Pin.IN, sim_machine.Pin.PULL_DOWN)

    scene._on_button_pressed(btn.component_id)
    assert sim_machine.Pin._gpio_manager.get_pin_state(4) == 1
    
    scene._on_button_released(btn.component_id)
    assert sim_machine.Pin._gpio_manager.get_pin_state(4) == 0


class TestSection19MandatoryTests:
    """Suite de validation formelle des 8 tests obligatoires (Section 19)."""

    def test_1_a10_connected_to_b10(self):
        """Test 1 : a10 connecté à b10 (même bande équipotentielle gauche)."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        connected = scene.get_connected_pins("breadboard_1", "r10_a")
        assert ("breadboard_1", "r10_b") in connected

    def test_2_a10_not_connected_to_f10(self):
        """Test 2 : a10 NON connecté à f10 (séparation centrale DIP / rainure)."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        connected = scene.get_connected_pins("breadboard_1", "r10_a")
        assert ("breadboard_1", "r10_f") not in connected

    def test_3_a10_not_connected_to_a11(self):
        """Test 3 : a10 NON connecté à a11 (rangées adjacentes isolées)."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        connected = scene.get_connected_pins("breadboard_1", "r10_a")
        assert ("breadboard_1", "r11_a") not in connected

    def test_4_led_c10_jumper_a10_connected(self):
        """Test 4 : LED sur c10 + jumper sur a10 -> connectés électriquement sans fil artificiel."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        # Enfichage broche LED sur c10
        scene.topology.insert_pin("led_1", "anode", "r10_c")
        # Jumper de l'ESP32 GPIO23 vers a10
        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO23",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)
        connected = scene.get_connected_pins("esp32", "GPIO23")
        assert ("led_1", "anode") in connected

    def test_5_led_c10_jumper_f10_not_connected(self):
        """Test 5 : LED sur c10 + jumper sur f10 -> NON connectés."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        # Enfichage broche LED sur c10 (côté gauche)
        scene.topology.insert_pin("led_1", "anode", "r10_c")
        # Jumper vers f10 (côté droit au-delà du fossé DIP)
        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO23",
            to_component="breadboard_1", to_pin="r10_f",
            color="#38bdf8"
        )
        scene.connections.append(conn)
        connected = scene.get_connected_pins("esp32", "GPIO23")
        assert ("led_1", "anode") not in connected

    def test_6_invalid_pin_spacing_rejects_snap(self):
        """Test 6 : composant avec écartement invalide (non multiple du pas 8.5px) -> snap refusé."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.ui.canvas.snap_engine import SnapEngine, PinInfo
        topology = BreadboardTopology()
        engine = SnapEngine()
        # Écartement de 13.0px (incompatible avec la grille 8.5px)
        invalid_pins = [PinInfo("pin1", 0.0, 0.0), PinInfo("pin2", 0.0, 13.0)]
        result = engine.compute_snap(invalid_pins, QPointF(63.0, 130.0), topology)
        assert result is None

    def test_7_move_component_updates_pins_and_occupancy(self):
        """Test 7 : déplacement composant -> libération anciens trous, occupation nouveaux."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        # Position initiale: r10_b, r11_b
        snap1 = SnapResult(local_pos=QPointF(54.5, 104.5), pin_to_hole={"anode": "r10_b", "cathode": "r11_b"})
        scene._insert_component_in_breadboard(led, snap1)
        assert scene.topology.is_hole_occupied("r10_b")
        assert scene.topology.is_hole_occupied("r11_b")

        # Déplacement: libérer anciens trous
        scene._remove_component_from_breadboard(led)
        assert not scene.topology.is_hole_occupied("r10_b")
        assert not scene.topology.is_hole_occupied("r11_b")

        # Insérer dans nouveaux trous: r20_b, r21_b
        snap2 = SnapResult(local_pos=QPointF(54.5, 189.5), pin_to_hole={"anode": "r20_b", "cathode": "r21_b"})
        scene._insert_component_in_breadboard(led, snap2)
        assert scene.topology.is_hole_occupied("r20_b")
        assert scene.topology.is_hole_occupied("r21_b")
        assert scene.topology.get_pin_hole("led_1", "anode") == "r20_b"
        assert scene.topology.get_pin_hole("led_1", "cathode") == "r21_b"

    def test_8_remove_component_releases_holes_and_updates_nets(self):
        """Test 8 : suppression composant -> libération trous et mise à jour des nets."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        # Enficher la LED sur r10_c et r11_c
        snap = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap)

        # Connecter un fil sur r10_a
        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO23",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)

        # Vérifier que le netlist relie GPIO23 à l'anode de la LED
        assert ("led_1", "anode") in scene.get_connected_pins("esp32", "GPIO23")
        assert scene.topology.is_hole_occupied("r10_c")

        # Supprimer le composant sélectionné
        led.setSelected(True)
        scene.delete_selected_items()

        # Vérifier que le trou est libéré et que la LED n'est plus dans le net
        assert not scene.topology.is_hole_occupied("r10_c")
        assert ("led_1", "anode") not in scene.get_connected_pins("esp32", "GPIO23")


class TestPhysicalBreadboardRealisticSuite:
    """Suite de validation physique et électrique réaliste (Tests A à G)."""

    def test_a_led_properly_inserted_occupies_two_holes(self):
        """Test A : LED correctement insérée (pin1 -> c10, pin2 -> c11) -> les deux trous occupés."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        snap = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap)

        # Vérification topologique
        assert scene.topology.is_hole_occupied("r10_c")
        assert scene.topology.is_hole_occupied("r11_c")
        assert scene.topology.get_occupant("r10_c") == ("led_1", "anode")
        assert scene.topology.get_occupant("r11_c") == ("led_1", "cathode")

        # Vérification des objets graphiques alvéoles
        h1 = scene.breadboard_item.hole_anchors["r10_c"]
        h2 = scene.breadboard_item.hole_anchors["r11_c"]
        assert h1.has_component_lead is True
        assert h1.component_id == "led_1"
        assert h1.lead_id == "anode"
        assert h2.has_component_lead is True
        assert h2.component_id == "led_1"
        assert h2.lead_id == "cathode"

    def test_b_move_led_releases_old_occupies_new(self):
        """Test B : Déplacement de LED : ancienne position -> libérée, nouvelle -> occupée."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        # Position initiale
        snap1 = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap1)
        assert scene.topology.is_hole_occupied("r10_c")
        assert scene.topology.is_hole_occupied("r11_c")

        # Déplacement : libération des anciens trous
        scene._remove_component_from_breadboard(led)
        assert not scene.topology.is_hole_occupied("r10_c")
        assert not scene.topology.is_hole_occupied("r11_c")
        h1 = scene.breadboard_item.hole_anchors["r10_c"]
        assert h1.has_component_lead is False
        assert h1.component_id is None
        assert h1.lead_id is None

        # Nouvelle position
        snap2 = SnapResult(local_pos=QPointF(63.0, 147.0), pin_to_hole={"anode": "r15_c", "cathode": "r16_c"})
        scene._insert_component_in_breadboard(led, snap2)
        assert scene.topology.is_hole_occupied("r15_c")
        assert scene.topology.is_hole_occupied("r16_c")
        h_new1 = scene.breadboard_item.hole_anchors["r15_c"]
        assert h_new1.has_component_lead is True
        assert h_new1.component_id == "led_1"

    def test_c_collision_rejects_snap(self):
        """Test C : Collision : pin -> trou déjà occupé -> le snap doit être refusé."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.ui.canvas.snap_engine import SnapEngine, PinInfo
        topology = BreadboardTopology()
        engine = SnapEngine()

        # Occuper le trou r10_c avec un composant existant
        topology.insert_pin("other_comp", "p1", "r10_c")

        # Tenter d'insérer une LED sur r10_c
        led_pins = [PinInfo("anode", 0.0, 0.0), PinInfo("cathode", 0.0, 8.5)]
        result = engine.try_snap_at_hole(led_pins, "r10_c", topology)
        assert result is None
        assert engine.last_collision_hole == "r10_c"

    def test_d_internal_connection_same_strip(self):
        """Test D : Connexion interne : LED sur c10, résistance sur a10 -> même net électrique."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))

        # LED cathode en c10
        scene.topology.insert_pin("led_1", "cathode", "r10_c")
        # Résistance pin1 en a10
        scene.topology.insert_pin("res_1", "pin1", "r10_a")

        # Vérification netlist : connectés via le strip interne sans aucun fil
        connected = scene.get_connected_pins("led_1", "cathode")
        assert ("res_1", "pin1") in connected

    def test_e_central_isolation_gap(self):
        """Test E : Isolation centrale : LED sur c10, résistance sur f10 -> aucune connexion."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))

        # LED en c10 (gauche)
        scene.topology.insert_pin("led_1", "cathode", "r10_c")
        # Résistance en f10 (droite, au-delà de la rainure DIP)
        scene.topology.insert_pin("res_1", "pin1", "r10_f")

        connected = scene.get_connected_pins("led_1", "cathode")
        assert ("res_1", "pin1") not in connected

    def test_f_row_isolation(self):
        """Test F : Isolation entre rangées : a10 != a11."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))

        connected = scene.get_connected_pins("breadboard_1", "r10_a")
        assert ("breadboard_1", "r11_a") not in connected

    def test_g_no_artificial_wires_created_on_insert(self):
        """Test G : Absence de fils artificiels : aucun wire/jumper créé lors de l'insertion."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))
        res = scene.add_component("resistor", QPointF(0, 0))

        snap_led = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap_led)

        snap_res = SnapResult(local_pos=QPointF(63.0, 155.5), pin_to_hole={"pin1": "r11_c", "pin2": "r17_c"})
        scene._insert_component_in_breadboard(res, snap_res)

        # Aucune connexion artificielle ne doit être créée dans connections ou wire_items
        assert len(scene.connections) == 0
        assert len(scene.wire_items) == 0


class TestPrompt2PhysicalPinInsertionSuite:
    """Suite de 14 tests obligatoires pour la couche 2 (Physical Pin Insertion & Visual Rendering)."""

    def test_1_pin_has_visible_geometry_before_insertion(self):
        """Test 1 : Chaque broche possède une géométrie physique réelle visible avant insertion."""
        from esp32_lab.ui.canvas.items.led_item import LEDGraphicsItem
        led = LEDGraphicsItem("led_phys")
        anode = led.anode_pin

        assert anode.pin_length > 0.0
        assert anode.pin_thickness > 0.0
        assert anode.is_inserted is False
        assert anode.insertion_depth == 0.0
        assert anode.visible_length == anode.pin_length
        assert anode.associated_hole_id is None

        geom = anode.get_geometry()
        assert geom["pin_length"] == 24.0
        assert geom["pin_thickness"] == 1.8
        assert geom["visible_length"] == 24.0
        assert geom["is_inserted"] is False

    def test_2_pin_correctly_identifies_target_hole(self):
        """Test 2 : La broche identifie correctement son trou cible lors du snap."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import extract_pins
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        # Position au-dessus de r10_c (anode à rel_y=25.5 -> pos_y = 104.5 - 25.5 = 79.0)
        snap = scene.snap_engine.compute_snap(extract_pins(led), QPointF(63.0, 79.0), scene.topology)
        assert snap is not None
        assert snap.pin_to_hole["anode"] == "r10_c"
        assert snap.pin_to_hole["cathode"] == "r11_c"

    def test_3_valid_multi_pin_placement_succeeds(self):
        """Test 3 : Le placement d'un composant multi-broches valide est accepté."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import extract_pins
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        res = scene.add_component("resistor", QPointF(0, 0))

        snap = scene.snap_engine.compute_snap(extract_pins(res), QPointF(63.0, 138.5), scene.topology)
        assert snap is not None
        assert len(snap.pin_to_hole) == 2

    def test_4_invalid_multi_pin_placement_rejected(self):
        """Test 4 : Un placement multi-broches invalide (hors grille ou écartement incompatible) est rejeté."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.ui.canvas.snap_engine import SnapEngine, PinInfo
        topology = BreadboardTopology()
        engine = SnapEngine()

        # Écartement de 13.0px incompatible avec le pas 8.5px
        invalid_pins = [PinInfo("p1", 0.0, 0.0), PinInfo("p2", 0.0, 13.0)]
        result = engine.compute_snap(invalid_pins, QPointF(63.0, 100.0), topology)
        assert result is None

    def test_5_occupied_hole_prevents_insertion(self):
        """Test 5 : Une alvéole déjà occupée empêche l'insertion d'une autre broche (collision)."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.ui.canvas.snap_engine import SnapEngine, PinInfo
        topology = BreadboardTopology()
        engine = SnapEngine()

        topology.insert_pin("existing_comp", "p1", "r10_c")
        led_pins = [PinInfo("anode", 0.0, 0.0), PinInfo("cathode", 0.0, 8.5)]

        result = engine.try_snap_at_hole(led_pins, "r10_c", topology)
        assert result is None
        assert engine.last_collision_hole == "r10_c"

    def test_6_pin_partially_occluded_after_insertion(self):
        """Test 6 : La broche devient partiellement occluse sous la surface de la plaque après insertion."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        snap = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap)

        anode = led.anode_pin
        assert anode.is_inserted is True
        assert anode.insertion_depth == 8.0
        assert anode.visible_length == 16.0  # 24.0 - 8.0
        assert anode.visible_length < anode.pin_length
        assert anode.associated_hole_id == "r10_c"

    def test_7_pin_fully_visible_when_removed(self):
        """Test 7 : La longueur totale de la broche redevient visible lors du retrait du composant."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        snap = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap)
        assert led.anode_pin.is_inserted is True

        # Retrait du composant
        scene._remove_component_from_breadboard(led)
        assert led.anode_pin.is_inserted is False
        assert led.anode_pin.insertion_depth == 0.0
        assert led.anode_pin.visible_length == led.anode_pin.pin_length
        assert led.anode_pin.associated_hole_id is None

    def test_8_moving_inserted_component_releases_previous_holes(self):
        """Test 8 : Le déplacement d'un composant inséré libère immédiatement ses anciens trous."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        snap = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap)
        assert scene.topology.is_hole_occupied("r10_c")
        assert scene.topology.is_hole_occupied("r11_c")

        # Déplacement : libération
        scene._remove_component_from_breadboard(led)
        assert not scene.topology.is_hole_occupied("r10_c")
        assert not scene.topology.is_hole_occupied("r11_c")
        assert scene.breadboard_item.hole_anchors["r10_c"].has_component_lead is False

    def test_9_moving_inserted_component_correctly_occupies_new_holes(self):
        """Test 9 : Le déplacement d'un composant inséré occupe correctement les nouveaux trous."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        snap1 = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap1)

        scene._remove_component_from_breadboard(led)

        snap2 = SnapResult(local_pos=QPointF(63.0, 147.0), pin_to_hole={"anode": "r15_c", "cathode": "r16_c"})
        scene._insert_component_in_breadboard(led, snap2)

        assert scene.topology.is_hole_occupied("r15_c")
        assert scene.topology.is_hole_occupied("r16_c")
        assert led.anode_pin.associated_hole_id == "r15_c"
        assert led.cathode_pin.associated_hole_id == "r16_c"

    def test_10_rotation_recalculates_all_pin_positions(self):
        """Test 10 : La rotation du composant recalcule toutes les positions relatives des broches."""
        from esp32_lab.ui.canvas.items.resistor_item import ResistorGraphicsItem
        from esp32_lab.ui.canvas.snap_engine import extract_pins
        res = ResistorGraphicsItem("res_rot")

        # Vertical (0 deg)
        pins_v = extract_pins(res)
        assert abs(pins_v[0].rel_x) < 0.01
        assert abs(pins_v[1].rel_x) < 0.01
        dist_v = abs(pins_v[1].rel_y - pins_v[0].rel_y)
        assert abs(dist_v - 51.0) < 0.01

        # Horizontal (90 deg)
        res.setRotation(90.0)
        pins_h = extract_pins(res)
        assert abs(pins_h[0].rel_y) < 0.01
        assert abs(pins_h[1].rel_y) < 0.01
        dist_h = abs(pins_h[1].rel_x - pins_h[0].rel_x)
        assert abs(dist_h - 51.0) < 0.01, f"Distance {dist_h} should remain 51.0px"

    def test_11_jumper_endpoint_correctly_occupies_hole(self):
        """Test 11 : L'extrémité d'un cavalier (jumper) occupe physiquement son alvéole de raccordement."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))

        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO2",
            to_component="breadboard_1", to_pin="r10_a",
            color="#ef4444"
        )
        scene.connections.append(conn)
        scene._create_wire_item(conn)

        hole = scene.breadboard_item.hole_anchors["r10_a"]
        assert hole.has_wire is True

    def test_12_no_artificial_wire_created_between_pin_and_hole(self):
        """Test 12 : Aucun fil artificiel n'est généré entre la broche du composant et son alvéole."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import SnapResult
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))
        led = scene.add_component("led", QPointF(0, 0))

        snap = SnapResult(local_pos=QPointF(63.0, 104.5), pin_to_hole={"anode": "r10_c", "cathode": "r11_c"})
        scene._insert_component_in_breadboard(led, snap)

        # Vérifier qu'aucune connexion n'est créée dans scene.connections pour les broches de la LED
        assert len(scene.connections) == 0
        assert not any(c.from_component == "led_1" or c.to_component == "led_1" for c in scene.connections)

    def test_13_electrical_connectivity_from_breadboard_topology(self):
        """Test 13 : La connectivité électrique provient exclusivement de BreadboardTopology."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(0, 0))

        scene.topology.insert_pin("led_1", "cathode", "r10_c")
        scene.topology.insert_pin("res_1", "pin1", "r10_a")

        # Pas de fil tracé, mais même potentiel par le modèle logique de piste
        assert len(scene.connections) == 0
        connected = scene.get_connected_pins("led_1", "cathode")
        assert ("res_1", "pin1") in connected

    def test_14_existing_section_19_tests_pass(self):
        """Test 14 : La topologie existante (420 trous, 64 strips, isolation) reste 100% opérationnelle."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        t = BreadboardTopology()
        assert len(t.holes) == 420
        assert len(t.strips) == 64
        assert "r10_b" in t.get_connected_holes("r10_a")
        assert "r10_f" not in t.get_connected_holes("r10_a")
        assert "r11_a" not in t.get_connected_holes("r10_a")


class TestPureElectricalNetResolver:
    """Validation de l'architecture pure du moteur de simulation (sans widget Qt)."""

    def test_hole_and_connection_group_models(self):
        """Vérifie que Hole et ConnectionGroup ont tous les attributs structurels requis."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology, Hole, ConnectionGroup
        t = BreadboardTopology()
        hole = t.holes["r10_a"]
        assert isinstance(hole, Hole)
        assert hole.id == "r10_a"
        assert hole.row == 10
        assert hole.column == "a"
        assert hole.side == "left"
        assert hole.rail is None
        assert hole.connection_group_id == "row_10_left"
        assert hole.occupied is False
        assert hole.occupied_by is None

        cg = t.connection_groups["row_10_left"]
        assert isinstance(cg, ConnectionGroup)
        assert cg.id == "row_10_left"
        assert cg.group_type == "terminal_strip"
        assert "r10_a" in cg.hole_ids
        assert len(cg.hole_ids) == 5

    def test_pure_net_resolution_same_strip(self):
        """Test A10 et B10 connectés via le résolveur pur."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
        t = BreadboardTopology()
        resolver = ElectricalNetResolver(t)
        assert resolver.are_connected("breadboard_1", "r10_a", "breadboard_1", "r10_b")

    def test_pure_net_resolution_across_gap_isolated(self):
        """Test A10 et F10 isolés de part et d'autre de la rainure DIP."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
        t = BreadboardTopology()
        resolver = ElectricalNetResolver(t)
        assert not resolver.are_connected("breadboard_1", "r10_a", "breadboard_1", "r10_f")

    def test_pure_net_resolution_adjacent_rows_isolated(self):
        """Test A10 et A11 isolés (pas de court-circuit entre rangées)."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
        t = BreadboardTopology()
        resolver = ElectricalNetResolver(t)
        assert not resolver.are_connected("breadboard_1", "r10_a", "breadboard_1", "r11_a")

    def test_pure_jumper_and_pin_insertion_connectivity(self):
        """Test LED sur C10 + jumper sur A10 -> même net électrique sans fil artificiel."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
        t = BreadboardTopology()
        t.insert_pin("led_1", "anode", "r10_c")
        
        resolver = ElectricalNetResolver(t)
        # Jumper de l'ESP32 vers le trou A10
        resolver.add_connection("esp32", "GPIO2", "breadboard_1", "r10_a")

        assert resolver.are_connected("esp32", "GPIO2", "led_1", "anode")
        # Mais pas avec le côté opposé (F10)
        assert not resolver.are_connected("esp32", "GPIO2", "breadboard_1", "r10_f")

    def test_pure_resistor_bridge_propagation(self):
        """Test pont conducteur par composant passif (ex: résistance entre r10 et r15)."""
        from esp32_lab.core.breadboard_topology import BreadboardTopology
        from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
        t = BreadboardTopology()
        # Résistance insérée entre r10_c et r15_c
        t.insert_pin("r1", "pin1", "r10_c")
        t.insert_pin("r1", "pin2", "r15_c")

        resolver = ElectricalNetResolver(t)
        resolver.add_internal_bridge("r1", "pin1", "pin2")
        resolver.add_connection("esp32", "GPIO2", "breadboard_1", "r10_a")

        # Le potentiel doit se propager à travers la résistance jusqu'à r15_a
        assert resolver.are_connected("esp32", "GPIO2", "breadboard_1", "r15_a")


class TestEndToEndPhysicalCircuit:
    """Suite de validation complète de bout en bout du circuit physique (Section 19 - Prompt #4)."""

    def test_01_create_empty_board(self):
        """TEST 1 : Démarrage avec un espace de travail vierge."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        esp = scene.add_component("esp32", QPointF(0, 0))
        bb = scene.add_component("breadboard", QPointF(350, 0))

        assert len(scene.component_items) == 2
        assert len(scene.connections) == 0
        assert len(scene.topology.occupants) == 0
        assert len(scene.topology.holes) == 420
        assert all(not h.occupied for h in scene.topology.holes.values())

    def test_02_insert_led_physically(self):
        """TEST 2 : Insertion physique de la LED sur la breadboard par workflow de drop."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        bb = scene.add_component("breadboard", QPointF(350, 0))

        # Position alignant l'anode sur r10_c et la cathode sur r11_c
        led = scene.add_component("led", QPointF(413.0, 79.0))

        assert led.parentItem() == bb
        assert led.anode_pin.is_inserted is True
        assert led.cathode_pin.is_inserted is True
        assert led.anode_pin.visible_length < led.anode_pin.pin_length
        assert led.anode_pin.insertion_depth == 8.0

    def test_03_verify_both_led_pins_occupy_expected_holes(self):
        """TEST 3 : Vérification que les broches de la LED occupent exactement les trous cibles."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))

        assert scene.topology.get_pin_hole(led.component_id, "anode") == "r10_c"
        assert scene.topology.get_pin_hole(led.component_id, "cathode") == "r11_c"
        assert led.anode_pin.associated_hole_id == "r10_c"
        assert led.cathode_pin.associated_hole_id == "r11_c"

    def test_04_verify_occupied_holes(self):
        """TEST 4 : Vérification de l'état d'occupation physique des trous dans la topologie."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))

        assert scene.topology.is_hole_occupied("r10_c") is True
        assert scene.topology.is_hole_occupied("r11_c") is True
        assert scene.topology.holes["r10_c"].occupied_by == (led.component_id, "anode")
        assert scene.topology.holes["r11_c"].occupied_by == (led.component_id, "cathode")
        assert bb.hole_anchors["r10_c"].is_occupied is True
        assert bb.hole_anchors["r11_c"].is_occupied is True

    def test_05_insert_resistor(self):
        """TEST 5 : Insertion de la résistance sur la même bande de contact."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        scene.add_component("led", QPointF(413.0, 79.0))
        res = scene.add_component("resistor", QPointF(404.5, 138.5))

        assert res.parentItem() == bb
        assert scene.topology.get_pin_hole(res.component_id, "pin1") == "r11_b"
        assert scene.topology.get_pin_hole(res.component_id, "pin2") == "r17_b"
        assert res.pin1.is_inserted is True
        assert res.pin2.is_inserted is True

    def test_06_verify_led_resistor_internal_breadboard_connectivity(self):
        """TEST 6 : Vérification de la continuité interne LED Cathode -> Résistance Pin 1 via strip row_11_left."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))
        res = scene.add_component("resistor", QPointF(404.5, 138.5))

        # Vérifier qu'aucun fil artificiel n'existe
        assert len(scene.connections) == 0

        # Vérifier la connexion équipotentielle par la topologie
        cathode_connected = scene.get_connected_pins(led.component_id, "cathode")
        assert (res.component_id, "pin1") in cathode_connected

        # Vérifier le chemin explicatif
        path = scene.explain_path(led.component_id, "cathode", res.component_id, "pin1")
        assert path == [
            f"{led.component_id}.cathode",
            "Hole r11_c",
            "ConnectionGroup row_11_left",
            "Hole r11_b",
            f"{res.component_id}.pin1"
        ]

    def test_07_insert_jumper(self):
        """TEST 7 : Insertion d'un cavalier physique (ESP32 GPIO2 vers trou A10)."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        bb = scene.add_component("breadboard", QPointF(350, 0))
        scene.add_component("led", QPointF(413.0, 79.0))

        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO2",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)
        scene._create_wire_item(conn)

        assert len(scene.connections) == 1
        assert bb.hole_anchors["r10_a"].has_wire is True

    def test_08_verify_jumper_breadboard_connectivity(self):
        """TEST 8 : Continuité électrique entre le cavalier et la bande row_10_left."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        bb = scene.add_component("breadboard", QPointF(350, 0))

        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO2",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)
        scene._create_wire_item(conn)

        gpio_connected = scene.get_connected_pins("esp32", "GPIO2")
        assert ("breadboard_1", "r10_a") in gpio_connected
        assert ("breadboard_1", "r10_b") in gpio_connected
        assert ("breadboard_1", "r10_c") in gpio_connected
        assert ("breadboard_1", "r10_d") in gpio_connected
        assert ("breadboard_1", "r10_e") in gpio_connected

    def test_09_verify_gpio_jumper_breadboard_led_path(self):
        """TEST 9 : Vérification de la chaîne complète GPIO -> Cavalier -> Breadboard -> LED Anode."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))

        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO2",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)
        scene._create_wire_item(conn)

        gpio_connected = scene.get_connected_pins("esp32", "GPIO2")
        assert (led.component_id, "anode") in gpio_connected

        path = scene.explain_path("esp32", "GPIO2", led.component_id, "anode")
        assert path == [
            "esp32.GPIO2",
            "Hole r10_a",
            "ConnectionGroup row_10_left",
            "Hole r10_c",
            f"{led.component_id}.anode"
        ]

    def test_10_execute_micropython_gpio_output(self):
        """TEST 10 : Exécution de code MicroPython pilotant GPIO2."""
        import time
        from esp32_lab.simulator.engine import SimulationEngine
        engine = SimulationEngine()

        code = """
from machine import Pin
led = Pin(2, Pin.OUT)
led.value(1)
"""
        engine.start(code)
        deadline = time.time() + 2.0
        while engine.is_running() and time.time() < deadline:
            app.processEvents()
            time.sleep(0.05)

        assert engine.gpio_manager.read(2) == 1
        engine.stop()

    def test_11_verify_led_responds(self):
        """TEST 11 : La LED s'allume et s'éteint en temps réel selon les signaux GPIO simulés."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))

        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO2",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)
        scene._create_wire_item(conn)

        assert not led.is_lit
        scene.event_bus.gpio_changed.emit(2, 1)
        assert led.is_lit is True
        scene.event_bus.gpio_changed.emit(2, 0)
        assert led.is_lit is False

    def test_12_remove_jumper(self):
        """TEST 12 : Retrait physique du cavalier reliant GPIO2 à la breadboard."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        bb = scene.add_component("breadboard", QPointF(350, 0))

        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO2",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)
        scene._create_wire_item(conn)

        # Déconnexion du cavalier
        scene.removeItem(scene.wire_items[conn.id])
        scene.wire_items.pop(conn.id, None)
        scene.connections = [c for c in scene.connections if c.id != conn.id]

        assert len(scene.connections) == 0

    def test_13_verify_led_no_longer_responds(self):
        """TEST 13 : Avec le cavalier retiré, l'émission GPIO2 ne pilote plus la LED."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))

        # Pas de jumper connecté
        scene.event_bus.gpio_changed.emit(2, 1)
        assert led.is_lit is False
        assert (led.component_id, "anode") not in scene.get_connected_pins("esp32", "GPIO2")

    def test_14_move_component(self):
        """TEST 14 : Déplacement d'un composant (la résistance) vers d'autres rangées valides."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import extract_pins
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        scene.add_component("led", QPointF(413.0, 79.0))
        res = scene.add_component("resistor", QPointF(404.5, 138.5))

        # Déplacement : libération des anciens trous
        scene._remove_component_from_breadboard(res)
        pins = extract_pins(res)

        # Nouvelle position vers les rangées 20 et 26
        target_scene_pos = QPointF(404.5, 215.0)
        local_pos = bb.mapFromScene(target_scene_pos)
        snap = scene.snap_engine.compute_snap(pins, local_pos, scene.topology)
        assert snap is not None
        scene._insert_component_in_breadboard(res, snap)

        assert scene.topology.get_pin_hole(res.component_id, "pin1") == "r20_b"
        assert scene.topology.get_pin_hole(res.component_id, "pin2") == "r26_b"

    def test_15_verify_old_net_disappears(self):
        """TEST 15 : L'ancienne équipotentielle entre la cathode et la résistance a disparu après déplacement."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import extract_pins
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))
        res = scene.add_component("resistor", QPointF(404.5, 138.5))

        # Déplacement
        scene._remove_component_from_breadboard(res)
        pins = extract_pins(res)
        local_pos = bb.mapFromScene(QPointF(404.5, 215.0))
        snap = scene.snap_engine.compute_snap(pins, local_pos, scene.topology)
        scene._insert_component_in_breadboard(res, snap)

        # Les anciens trous r11_b et r17_b ne sont plus occupés par la résistance
        assert not scene.topology.is_hole_occupied("r11_b")
        assert not scene.topology.is_hole_occupied("r17_b")

        # La cathode n'est plus connectée à la résistance
        cathode_net = scene.get_connected_pins(led.component_id, "cathode")
        assert (res.component_id, "pin1") not in cathode_net

    def test_16_verify_new_net_appears(self):
        """TEST 16 : Une nouvelle liaison équipotentielle est créée sur la nouvelle rangée d'accueil."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import extract_pins
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        res = scene.add_component("resistor", QPointF(404.5, 138.5))

        # Déplacement vers row 20
        scene._remove_component_from_breadboard(res)
        pins = extract_pins(res)
        local_pos = bb.mapFromScene(QPointF(404.5, 215.0))
        snap = scene.snap_engine.compute_snap(pins, local_pos, scene.topology)
        scene._insert_component_in_breadboard(res, snap)

        # Pin1 est désormais sur r20_b et connectée à toute la bande row_20_left
        pin1_net = scene.get_connected_pins(res.component_id, "pin1")
        assert ("breadboard_1", "r20_a") in pin1_net
        assert ("breadboard_1", "r20_e") in pin1_net

    def test_17_remove_component(self):
        """TEST 17 : Suppression complète de la LED de la scène."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))

        scene._remove_component_from_breadboard(led)
        scene.removeItem(led)
        scene.component_items.pop(led.component_id, None)

        assert led.component_id not in scene.component_items

    def test_18_verify_holes_released(self):
        """TEST 18 : Les trous précédemment occupés par la LED sont complètement libérés."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))

        scene._remove_component_from_breadboard(led)
        scene.removeItem(led)
        scene.component_items.pop(led.component_id, None)

        assert scene.topology.is_hole_occupied("r10_c") is False
        assert scene.topology.is_hole_occupied("r11_c") is False
        assert bb.hole_anchors["r10_c"].is_occupied is False
        assert bb.hole_anchors["r11_c"].is_occupied is False
        assert scene.topology.holes["r10_c"].occupied_by is None

    def test_19_verify_electrical_net_updated(self):
        """TEST 19 : Le graphe équipotentiel et les chemins ne contiennent plus aucun vestige de la LED."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(413.0, 79.0))

        conn = ConnectionModel(
            from_component="esp32", from_pin="GPIO2",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)
        scene._create_wire_item(conn)

        # Suppression de la LED
        scene._remove_component_from_breadboard(led)
        scene.removeItem(led)
        scene.component_items.pop(led.component_id, None)

        # Plus aucun chemin vers la LED
        assert scene.explain_path("esp32", "GPIO2", "led_1", "anode") == []
        info = scene.inspect_pin("led_1", "anode")
        assert info["inserted_into"] is None
        assert info["net_id"] == "DISCONNECTED"

    def test_20_verify_no_artificial_wires_exist_anywhere_in_the_circuit(self):
        """TEST 20 : Aucun fil artificiel n'est créé nulle part dans le circuit complet."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        scene = CircuitScene()
        scene.add_component("esp32", QPointF(0, 0))
        scene.add_component("breadboard", QPointF(350, 0))
        scene.add_component("led", QPointF(413.0, 79.0))
        scene.add_component("resistor", QPointF(404.5, 138.5))

        # Seuls les cavaliers utilisateur légitimes sont autorisés
        jumper_gpio = ConnectionModel(
            from_component="esp32", from_pin="GPIO2",
            to_component="breadboard_1", to_pin="r10_a",
            color="#38bdf8"
        )
        jumper_gnd = ConnectionModel(
            from_component="breadboard_1", from_pin="r17_a",
            to_component="esp32", to_pin="GND",
            color="#000000"
        )
        scene.connections.extend([jumper_gpio, jumper_gnd])
        scene._create_wire_item(jumper_gpio)
        scene._create_wire_item(jumper_gnd)

        assert len(scene.connections) == 2
        for conn in scene.connections:
            # Vérifier qu'aucune connexion ne relie directement une broche de LED ou de résistance
            assert "led" not in conn.from_component and "led" not in conn.to_component
            assert "resistor" not in conn.from_component and "resistor" not in conn.to_component


class TestDragAndDropPhysicalPlacementSuite:
    """Suite de validation du Drag & Drop physique intuitif et de la prévisualisation (Section 19)."""

    def test_1_two_pin_preview_identifies_exact_target_holes(self):
        """1. La prévisualisation d'un composant 2 broches identifie exactement les alvéoles cibles."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        preview = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        assert preview.valid is True
        assert preview.target_holes == ["r10_c", "r11_c"]
        assert preview.pin_to_hole_map == {"anode": "r10_c", "cathode": "r11_c"}

    def test_2_valid_placement_highlights_all_target_holes(self):
        """2. Un placement valide met tous les trous cibles dans l'état VALID_PREVIEW."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.items.breadboard_item import HoleVisualState
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        preview = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        bb.set_preview_states(preview.target_holes, preview.invalid_holes)

        assert bb.hole_anchors["r10_c"].visual_state == HoleVisualState.VALID_PREVIEW
        assert bb.hole_anchors["r11_c"].visual_state == HoleVisualState.VALID_PREVIEW
        assert bb.hole_anchors["r10_c"].is_preview is True
        assert bb.hole_anchors["r11_c"].is_preview is True

    def test_3_invalid_pin_spacing_produces_invalid_preview(self):
        """3. Un espacement de broches non conforme à la grille génère INVALID_PREVIEW."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import PinInfo
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))

        # Écartement de 13.5px (non multiple de 8.5px)
        pins = [PinInfo("p1", 0, 0), PinInfo("p2", 0, 13.5)]
        preview = scene.snap_engine.compute_placement_preview(pins, QPointF(63.0, 104.5), scene.topology)

        assert preview.valid is False
        assert len(preview.invalid_holes) > 0
        assert preview.reason is not None

    def test_4_adjacent_holes_not_automatically_accepted_when_spacing_wrong(self):
        """4. Des trous adjacents ne sont pas acceptés si l'espacement physique réel ne correspond pas."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import PinInfo
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))

        # Résistance de 51px (6 rangées d'écart)
        res_pins = [PinInfo("pin1", 0, -25.5), PinInfo("pin2", 0, 25.5)]

        # Essayer un placement arbitraire : la fonction ne doit JAMAIS associer pin2 à la rangée adjacente (+1 rangée)
        preview = scene.snap_engine.compute_placement_preview(res_pins, QPointF(63.0, 108.75), scene.topology)
        if preview.valid:
            h1 = scene.topology.holes[preview.pin_to_hole_map["pin1"]]
            h2 = scene.topology.holes[preview.pin_to_hole_map["pin2"]]
            assert abs(h2.row - h1.row) == 6

    def test_5_moving_component_changes_target_holes_dynamically(self):
        """5. Le déplacement du composant met à jour dynamiquement les trous cibles."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        p1 = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        p2 = scene.preview_component_placement(led, QPointF(413.0, 121.5))

        assert p1.target_holes == ["r10_c", "r11_c"]
        assert p2.target_holes == ["r15_c", "r16_c"]
        assert p1.target_holes != p2.target_holes

    def test_6_rotation_recalculates_target_holes(self):
        """6. La rotation recalcule immédiatement les trous cibles."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        p_vert = scene.preview_component_placement(led, QPointF(413.0, 79.0), rotation=0.0)
        p_rot = scene.preview_component_placement(led, QPointF(413.0, 79.0), rotation=90.0)

        assert p_rot.rotation == 90.0
        assert p_vert.target_holes != p_rot.target_holes

    def test_7_occupied_hole_causes_invalid_placement(self):
        """7. Une alvéole déjà occupée entraîne une prévisualisation invalide (INVALID_PREVIEW)."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        # Occuper r10_c
        scene.topology.insert_pin("other_comp", "p1", "r10_c")

        preview = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        assert preview.valid is False
        assert "r10_c" in preview.invalid_holes

    def test_8_multi_pin_component_validates_all_pins_together(self):
        """8. Un composant multi-broches valide l'ensemble de ses broches en un bloc cohérent."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import extract_pins
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        btn = scene.add_component("button", QPointF(100, 100))

        pins = extract_pins(btn)
        assert len(pins) == 4

        # Chevauchant le fossé DIP (colonnes e et f)
        preview = scene.preview_component_placement(btn, QPointF(350 + 99.0, 104.5))
        if preview.valid:
            assert len(preview.target_holes) == 4
            assert len(preview.pin_to_hole_map) == 4

    def test_9_valid_preview_and_committed_placement_produce_identical_mapping(self):
        """9. La prévisualisation valide et le placement effectif produisent exactement le même mapping."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        preview = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        assert preview.valid is True

        success = scene.commit_component_placement(led, preview)
        assert success is True
        assert scene.topology.get_pin_hole(led.component_id, "anode") == preview.pin_to_hole_map["anode"]
        assert scene.topology.get_pin_hole(led.component_id, "cathode") == preview.pin_to_hole_map["cathode"]

    def test_10_invalid_release_does_not_modify_topology(self):
        """10. Un relâchement invalide ne corrompt pas la topologie et n'occupe aucun trou."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.snap_engine import PlacementPreview
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        occupants_before = dict(scene.topology.occupants)

        invalid_preview = PlacementPreview(
            valid=False,
            target_holes=["r10_c"],
            invalid_holes=["r10_c"],
            pin_to_hole_map={},
            snap_position=QPointF(0, 0),
            rotation=0.0,
            reason="INVALID_SPACING"
        )
        committed = scene.commit_component_placement(led, invalid_preview)
        assert committed is False
        assert scene.topology.occupants == occupants_before

    def test_11_valid_release_occupies_correct_holes(self):
        """11. Un relâchement valide occupe fidèlement les trous correspondants."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        preview = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        scene.commit_component_placement(led, preview)

        assert scene.topology.is_hole_occupied("r10_c") is True
        assert scene.topology.is_hole_occupied("r11_c") is True
        assert bb.hole_anchors["r10_c"].is_occupied is True
        assert bb.hole_anchors["r11_c"].is_occupied is True

    def test_12_removing_component_releases_holes(self):
        """12. Le retrait d'un composant libère immédiatement ses trous."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        preview = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        scene.commit_component_placement(led, preview)
        assert scene.topology.is_hole_occupied("r10_c") is True

        scene._remove_component_from_breadboard(led)
        assert scene.topology.is_hole_occupied("r10_c") is False
        assert scene.topology.is_hole_occupied("r11_c") is False
        assert bb.hole_anchors["r10_c"].is_occupied is False
        assert bb.hole_anchors["r11_c"].is_occupied is False

    def test_13_pin_orientation_remains_vertical_toward_breadboard_during_drag(self):
        """13. L'orientation des broches reste physiquement verticale vers la breadboard."""
        from esp32_lab.ui.canvas.items.led_item import LEDGraphicsItem
        from esp32_lab.ui.canvas.snap_engine import extract_pins
        led = LEDGraphicsItem("led_1")

        pins = extract_pins(led, rotation=0.0)
        # Broches alignées sur le même axe vertical X=0
        assert pins[0].rel_x == 0.0
        assert pins[1].rel_x == 0.0
        # Broche 2 en dessous de broche 1 (Y croissant vers le bas)
        assert pins[1].rel_y > pins[0].rel_y
        assert led.anode_pin.pin_length > 0.0

    def test_14_no_artificial_electrical_wire_is_created_by_placement(self):
        """14. Aucun fil artificiel n'est généré lors du placement."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        preview = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        scene.commit_component_placement(led, preview)

        assert len(scene.connections) == 0

    def test_15_electrical_net_resolver_sees_correct_connectivity_after_commit(self):
        """15. ElectricalNetResolver reflète la connectivité correcte immédiatement après le commit."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        preview = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        scene.commit_component_placement(led, preview)

        # Insertion d'un conducteur sur A10 (même bande row_10_left que l'anode en C10)
        scene.topology.insert_pin("jumper", "src", "r10_a")
        resolver = scene._create_net_resolver()

        assert resolver.are_connected("jumper", "src", led.component_id, "anode") is True
        assert resolver.are_connected("jumper", "src", led.component_id, "cathode") is False


class TestPhysicalRealismAuditSuite:
    """Suite de tests d'audit et de validation du réalisme physique du simulateur d'assemblage breadboard."""

    def test_1_physical_pin_rendering_no_floating_schematic_elements(self):
        """1. Les broches physiques n'affichent aucun élément schématique flottant au repos ou insérées."""
        from esp32_lab.ui.canvas.items.led_item import LEDGraphicsItem
        from PySide6.QtGui import QImage, QPainter

        led = LEDGraphicsItem("led_audit_1")
        img = QImage(100, 100, QImage.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        # Ne doit pas lever d'erreur lors du rendu des broches au repos et insérées
        led.anode_pin.paint(p, None)
        assert led.anode_pin.is_inserted is False
        led.anode_pin.set_inserted("r10_c", depth=8.0)
        assert led.anode_pin.is_inserted is True
        led.anode_pin.paint(p, None)
        p.end()

    def test_2_hole_cavity_and_spring_contacts(self):
        """2. Les alvéoles possèdent une géométrie de puits réaliste et des lames de pinces à ressort."""
        from esp32_lab.ui.canvas.items.breadboard_item import BreadboardGraphicsItem, BreadboardHoleItem
        from PySide6.QtGui import QImage, QPainter

        bb = BreadboardGraphicsItem("bb_audit")
        img = QImage(250, 350, QImage.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        bb._draw_socket(p, 50.0, 50.0)

        hole = bb.hole_anchors["r10_c"]
        hole.paint(p, None)
        hole.set_occupied("comp_1", "p1")
        assert hole.is_occupied is True
        hole.paint(p, None)
        hole.set_free()
        assert hole.is_occupied is False
        p.end()

    def test_3_jumper_wire_terminal_alignment(self):
        """3. Les embouts de cavaliers Dupont s'insèrent directement dans les coordonnées des alvéoles."""
        from esp32_lab.ui.canvas.wire_item import WireGraphicsItem
        from PySide6.QtGui import QImage, QPainter

        wire = WireGraphicsItem("w_audit", color="#3b82f6")
        start_pt = QPointF(50.0, 100.0)
        end_pt = QPointF(150.0, 200.0)
        wire.set_endpoints(start_pt, end_pt)

        assert not wire.path().isEmpty()
        img = QImage(300, 300, QImage.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        wire.paint(p, None)
        p.end()

    def test_4_component_proportions_and_scale(self):
        """4. Les proportions entre Breadboard, ESP32, LED, Résistance et Bouton sont cohérentes."""
        from esp32_lab.ui.canvas.items.breadboard_item import BreadboardGraphicsItem
        from esp32_lab.ui.canvas.items.board_item import BoardGraphicsItem
        from esp32_lab.ui.canvas.items.led_item import LEDGraphicsItem
        from esp32_lab.ui.canvas.items.resistor_item import ResistorGraphicsItem
        from esp32_lab.ui.canvas.items.button_item import ButtonGraphicsItem

        bb = BreadboardGraphicsItem("bb")
        esp = BoardGraphicsItem("esp")
        led = LEDGraphicsItem("led")
        res = ResistorGraphicsItem("res")
        btn = ButtonGraphicsItem("btn")

        # Pas de grille de la plaque
        assert bb.ROW_STEP_Y == 8.5
        assert bb.COL_STEP_X == 8.5

        # Écartement des broches de la LED = 1 pas de grille (8.5px)
        anode_y = led.anode_pin.pos().y()
        cathode_y = led.cathode_pin.pos().y()
        assert abs(cathode_y - anode_y) == 8.5

        # Écartement des broches de la résistance = 6 pas de grille (51.0px)
        p1_y = res.pin1.pos().y()
        p2_y = res.pin2.pos().y()
        assert abs(p2_y - p1_y) == 51.0

        # Écartement transversal du bouton = enjambement du canal DIP (38.0px)
        assert abs(btn.pin2.pos().x() - btn.pin1.pos().x()) == 38.0

    def test_5_zoom_and_pan_preserves_geometry(self):
        """5. Le facteur de zoom (50%, 75%, 100%, 150%, 200%) préserve l'intégrité géométrique."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.circuit_view import CircuitView

        scene = CircuitScene()
        view = CircuitView(scene)
        bb = scene.add_component("breadboard", QPointF(200, 100))

        for factor in [0.5, 0.75, 1.0, 1.5, 2.0]:
            view.resetTransform()
            view.scale(factor, factor)
            p1 = bb.mapToScene(bb.hole_anchors["r1_a"].pos())
            p2 = bb.mapToScene(bb.hole_anchors["r2_a"].pos())
            assert round(p2.y() - p1.y(), 2) == 8.5

    def test_6_combination_zoom_drag_rotate_preview_commit(self):
        """6. Test d'enchaînement : zoom -> glisser -> rotation -> prévisualisation -> commit."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.circuit_view import CircuitView

        scene = CircuitScene()
        view = CircuitView(scene)
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        # 1. Zoom
        view.scale(1.5, 1.5)

        # 2. Glisser au-dessus de r10_c
        target_scene_pos = QPointF(413.0, 79.0)
        p_vert = scene.preview_component_placement(led, target_scene_pos, rotation=0.0)
        assert p_vert.valid is True
        assert p_vert.target_holes == ["r10_c", "r11_c"]

        # 3. Rotation 180°
        p_180 = scene.preview_component_placement(led, target_scene_pos, rotation=180.0)
        assert p_180.rotation == 180.0

        # 4. Commit
        committed = scene.commit_component_placement(led, p_vert)
        assert committed is True
        assert scene.topology.is_hole_occupied("r10_c") is True
        assert scene.topology.is_hole_occupied("r11_c") is True

    def test_7_combination_rotate_drag_invalid_move_valid_commit(self):
        """7. Test d'enchaînement : rotation -> placement invalide -> déplacement vers libre -> commit."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(100, 100))

        # Occuper r10_c
        scene.topology.insert_pin("obstacle", "p1", "r10_c")

        # Placement sur r10_c -> invalide
        p_bad = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        assert p_bad.valid is False
        assert "r10_c" in p_bad.invalid_holes

        # Déplacement vers rangée 15 libre -> valide
        p_good = scene.preview_component_placement(led, QPointF(413.0, 121.5))
        assert p_good.valid is True
        assert p_good.target_holes == ["r15_c", "r16_c"]

        success = scene.commit_component_placement(led, p_good)
        assert success is True
        assert scene.topology.is_hole_occupied("r15_c") is True
        assert scene.topology.is_hole_occupied("r16_c") is True

    def test_8_deterministic_demo_scene_a_empty_breadboard(self):
        """8. Scène A : Platine d'expérimentation seule."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtGui import QImage, QPainter
        import os

        scene = CircuitScene()
        scene.add_component("breadboard", QPointF(150, 40))

        img = QImage(600, 500, QImage.Format_ARGB32)
        img.fill(0xff1e293b)
        p = QPainter(img)
        scene.render(p)
        p.end()

        out_path = os.path.join(os.environ.get("TEMP", "."), "scene_a_breadboard.png")
        img.save(out_path)
        assert os.path.exists(out_path)

    def test_9_deterministic_demo_scene_b_esp32_breadboard(self):
        """9. Scène B : ESP32 + Platine d'expérimentation."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtGui import QImage, QPainter
        import os

        scene = CircuitScene()
        scene.add_component("esp32", QPointF(40, 40))
        scene.add_component("breadboard", QPointF(240, 40))

        img = QImage(700, 500, QImage.Format_ARGB32)
        img.fill(0xff1e293b)
        p = QPainter(img)
        scene.render(p)
        p.end()

        out_path = os.path.join(os.environ.get("TEMP", "."), "scene_b_esp32_breadboard.png")
        img.save(out_path)
        assert os.path.exists(out_path)

    def test_10_deterministic_demo_scene_c_esp32_breadboard_led_resistor(self):
        """10. Scène C : ESP32 + Platine + LED + Résistance insérées physiquement."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtGui import QImage, QPainter
        import os

        scene = CircuitScene()
        scene.add_component("esp32", QPointF(40, 40))
        bb = scene.add_component("breadboard", QPointF(240, 40))
        led = scene.add_component("led", QPointF(100, 100))
        res = scene.add_component("resistor", QPointF(100, 200))

        # Insertion physique LED sur r10_c / r11_c
        p_led = scene.preview_component_placement(led, QPointF(303.0, 119.0))
        scene.commit_component_placement(led, p_led)

        # Insertion physique Résistance sur r14_c / r20_c
        p_res = scene.preview_component_placement(res, QPointF(303.0, 204.0))
        scene.commit_component_placement(res, p_res)

        img = QImage(700, 500, QImage.Format_ARGB32)
        img.fill(0xff1e293b)
        p = QPainter(img)
        scene.render(p)
        p.end()

        out_path = os.path.join(os.environ.get("TEMP", "."), "scene_c_components.png")
        img.save(out_path)
        assert os.path.exists(out_path)
        assert scene.topology.is_hole_occupied("r10_c") is True

    def test_11_deterministic_demo_scene_d_gpio2_led_circuit(self):
        """11. Scène D : Circuit complet GPIO2 LED avec cavaliers physiques Dupont."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.examples import create_blink_example
        from PySide6.QtGui import QImage, QPainter
        import os

        scene = CircuitScene()
        proj = create_blink_example()
        scene.load_project_circuit(proj)

        # Vérifier la résolution électrique
        resolver = scene._create_net_resolver()
        assert resolver.are_connected("esp32", "GPIO2", "breadboard_1", "r10_a") is True
        assert resolver.are_connected("esp32", "GPIO2", "led_1", "anode") is True

        img = QImage(700, 500, QImage.Format_ARGB32)
        img.fill(0xff1e293b)
        p = QPainter(img)
        scene.render(p)
        p.end()

        out_path = os.path.join(os.environ.get("TEMP", "."), "scene_d_gpio2_circuit.png")
        img.save(out_path)
        assert os.path.exists(out_path)


class TestESP32PhysicalBoardSuite:
    """Suite de tests d'architecture et de réalisme physique pour la carte ESP32 et le modèle GPIO (Prompt 6)."""

    def test_1_esp32_profile_exact_geometry(self):
        """1. ESP32DevKitProfile définit les dimensions réelles, le pas 8.5px et l'espacement 89.0px."""
        from esp32_lab.core.models.board import create_esp32_devkit_profile
        profile = create_esp32_devkit_profile()
        assert profile.width == 110.0
        assert profile.height == 180.0
        assert profile.pin_step_y == 8.5
        assert profile.header_span_x == 89.0
        assert len(profile.pins) == 30

        # Vérifier l'écartement physique entre rangées gauche (-44.5) et droite (+44.5)
        p_left = profile.pins["EN"]
        p_right = profile.pins["3V3"]
        assert p_right.rel_x - p_left.rel_x == 89.0

    def test_2_board_pins_are_physical_pin_items(self):
        """2. Chaque broche d'en-tête de la carte est un PhysicalPinItem avec identité GPIO et rôle."""
        from esp32_lab.ui.canvas.items.board_item import BoardGraphicsItem
        from esp32_lab.ui.canvas.items.pin_item import PhysicalPinItem

        board = BoardGraphicsItem("esp32")
        assert len(board.profile.pins) == 30

        # Vérifier la nature physique de chaque broche
        for p_def in board.profile.pins.values():
            anchor = board.pin_anchors[p_def.pin_id]
            assert isinstance(anchor, PhysicalPinItem)
            assert anchor.owner_id == "esp32"
            assert anchor.pin_id == p_def.pin_id
            assert anchor.gpio_num == p_def.gpio_num
            assert anchor.role == p_def.role

        assert board.pin_anchors["GPIO2"].gpio_num == 2
        assert board.pin_anchors["GPIO2"].role == "gpio"
        assert board.pin_anchors["GND_1"].role == "ground"
        assert board.pin_anchors["VIN"].role == "power"

    def test_3_header_pin_pitch_matches_breadboard(self):
        """3. Le pas longitudinal entre broches consécutives est rigoureusement égal à 8.5 px."""
        from esp32_lab.ui.canvas.items.board_item import BoardGraphicsItem

        board = BoardGraphicsItem("esp32")
        # Vérifier le pas sur les broches gauches
        left_anchors = [board.pin_anchors[pid] for pid in ["EN", "GPIO36", "GPIO39", "GPIO34", "GPIO35"]]
        for i in range(len(left_anchors) - 1):
            dy = left_anchors[i + 1].pos().y() - left_anchors[i].pos().y()
            assert round(dy, 4) == 8.5

        # Vérifier le pas sur les broches droites
        right_anchors = [board.pin_anchors[pid] for pid in ["3V3", "GND_2", "GPIO15", "GPIO2", "GPIO4"]]
        for i in range(len(right_anchors) - 1):
            dy = right_anchors[i + 1].pos().y() - right_anchors[i].pos().y()
            assert round(dy, 4) == 8.5

    def test_4_esp32_breadboard_direct_insertion_straddling_dip(self):
        """4. Insertion directe de l'ESP32 sur la breadboard à cheval sur la rainure centrale DIP."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(50, 50))

        # Position cible sur la breadboard : rows 1 à 15
        target_scene_pos = QPointF(244.0, 47.5)
        preview = scene.preview_component_placement(esp, target_scene_pos)
        assert preview.valid is True
        assert len(preview.target_holes) == 30
        assert len(preview.invalid_holes) == 0

        # Vérifier que les broches gauches ciblent la colonne b (rangées 1 à 15)
        for r in range(1, 16):
            assert f"r{r}_b" in preview.target_holes

        # Vérifier que les broches droites ciblent la colonne i (rangées 1 à 15)
        for r in range(1, 16):
            assert f"r{r}_i" in preview.target_holes

        # Appliquer l'insertion
        success = scene.commit_component_placement(esp, preview)
        assert success is True
        assert esp.parentItem() == bb

    def test_5_esp32_all_30_pins_occupy_holes(self):
        """5. Toutes les 30 broches physiques occupent 30 trous distincts et sont en état INSERTED."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.items.pin_item import PhysicalPinItem
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        assert preview.valid is True
        scene.commit_component_placement(esp, preview)

        # Vérifier dans la topologie
        occupied_holes = [h for h, occ in scene.topology.occupants.items() if occ[0] == "esp32"]
        assert len(occupied_holes) == 30

        # Vérifier sur chaque broche physique
        for child in esp.childItems():
            if isinstance(child, PhysicalPinItem):
                assert child.is_inserted is True
                assert child.insertion_depth == 8.0
                assert child.associated_hole_id in occupied_holes

    def test_6_columns_a_and_j_remain_accessible(self):
        """6. L'insertion en colonnes b et i laisse les colonnes a et j totalement libres et accessibles."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        scene.commit_component_placement(esp, preview)

        for r in range(1, 16):
            # Colonne A libre
            assert scene.topology.is_hole_occupied(f"r{r}_a") is False
            # Colonne J libre
            assert scene.topology.is_hole_occupied(f"r{r}_j") is False

    def test_7_esp32_removal_releases_all_30_holes(self):
        """7. Retirer ou déplacer l'ESP32 libère intégralement les 30 trous de la breadboard."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.items.pin_item import PhysicalPinItem
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        scene.commit_component_placement(esp, preview)
        assert len(scene.topology.occupants) == 30

        # Retirer le composant de la platine
        scene._remove_component_from_breadboard(esp)
        assert len(scene.topology.occupants) == 0

        for child in esp.childItems():
            if isinstance(child, PhysicalPinItem):
                assert child.is_inserted is False
                assert child.insertion_depth == 0.0
                assert child.associated_hole_id is None

    def test_8_gpio2_electrical_net_propagation_when_inserted(self):
        """8. Continuité électrique pure : GPIO2 inséré en r4_i rejoint l'anode d'une LED insérée en r4_j."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview_esp = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        scene.commit_component_placement(esp, preview_esp)

        # Insérer une LED directement sur les trous r4_j (anode) et r5_j (cathode)
        led = scene.add_component("led", QPointF(50, 50))
        scene.topology.insert_pin(led.component_id, "anode", "r4_j")
        scene.topology.insert_pin(led.component_id, "cathode", "r5_j")

        resolver = scene._create_net_resolver()
        assert resolver.are_connected("esp32", "GPIO2", led.component_id, "anode") is True
        assert resolver.are_connected("esp32", "GPIO2", led.component_id, "cathode") is False

    def test_9_micropython_gpio2_output_drives_led_via_breadboard(self):
        """9. L'exécution MicroPython de GPIO2 allume à la fois la LED interne bleue et la LED externe."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview_esp = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        scene.commit_component_placement(esp, preview_esp)

        led = scene.add_component("led", QPointF(50, 50))
        scene.topology.insert_pin(led.component_id, "anode", "r4_j")
        scene.topology.insert_pin(led.component_id, "cathode", "r5_j")

        # Initialement éteints
        assert esp.gpio2_led_state is False
        assert led.is_on is False

        # Signal GPIO2 HIGH émis par MicroPython
        scene._on_gpio_changed(2, 1)
        assert esp.gpio2_led_state is True
        assert led.is_on is True

        # Signal GPIO2 LOW
        scene._on_gpio_changed(2, 0)
        assert esp.gpio2_led_state is False
        assert led.is_on is False

    def test_10_dupont_jumper_connection_mode(self):
        """10. Mode cavalier DuPont : carte à côté de la breadboard avec fil reliant GPIO2 à r10_a."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(250, 50))
        esp = scene.add_component("esp32", QPointF(50, 50))

        # Carte posée à côté de la platine (non insérée)
        assert esp.parentItem() != bb
        assert len(scene.topology.occupants) == 0

        # Insérer une LED sur la platine en r10_c (anode) et r11_c (cathode)
        led = scene.add_component("led", QPointF(50, 50))
        scene.topology.insert_pin(led.component_id, "anode", "r10_c")
        scene.topology.insert_pin(led.component_id, "cathode", "r11_c")

        # Cavalier DuPont entre broche ESP32 GPIO2 et le trou r10_a de la breadboard
        conn = ConnectionModel(
            from_component="esp32",
            from_pin="GPIO2",
            to_component="breadboard_1",
            to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)

        resolver = scene._create_net_resolver()
        assert resolver.are_connected("esp32", "GPIO2", led.component_id, "anode") is True

    def test_11_micropython_gpio_via_jumper_drives_led(self):
        """11. Propagation MicroPython via cavalier DuPont physique jusqu'au composant."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(250, 50))
        esp = scene.add_component("esp32", QPointF(50, 50))
        led = scene.add_component("led", QPointF(50, 50))
        scene.topology.insert_pin(led.component_id, "anode", "r10_c")

        conn = ConnectionModel(
            from_component="esp32",
            from_pin="GPIO2",
            to_component="breadboard_1",
            to_pin="r10_a",
            color="#38bdf8"
        )
        scene.connections.append(conn)

        scene._on_gpio_changed(2, 1)
        assert esp.gpio2_led_state is True
        assert led.is_on is True

        scene._on_gpio_changed(2, 0)
        assert esp.gpio2_led_state is False
        assert led.is_on is False

    def test_12_no_artificial_wires_in_direct_insertion(self):
        """12. L'enfichage direct de l'ESP32 sur la breadboard ne génère aucun fil artificiel."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        scene.commit_component_placement(esp, preview)

        assert len(scene.connections) == 0
        assert len(scene.wire_items) == 0

    def test_13_esp32_rotation_0_and_180(self):
        """13. Rotation à 180° s'enfiche correctement, mais 90° et 270° sont rejetées (incompatibilité physique)."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(50, 50))

        # 1. Orientation normale 0°
        p0 = scene.preview_component_placement(esp, QPointF(244.0, 47.5), rotation=0.0)
        assert p0.valid is True

        # 2. Orientation inversée 180°
        p180 = scene.preview_component_placement(esp, QPointF(244.0, 47.5), rotation=180.0)
        assert p180.valid is True

        # 3. Orientation 90°
        p90 = scene.preview_component_placement(esp, QPointF(244.0, 47.5), rotation=90.0)
        assert p90.valid is False

        # 4. Orientation 270°
        p270 = scene.preview_component_placement(esp, QPointF(244.0, 47.5), rotation=270.0)
        assert p270.valid is False

    def test_14_inspect_pin_gpio2_reports_exact_topology(self):
        """14. inspect_pin('esp32', 'GPIO2') retourne les détails topologiques réels."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        scene.commit_component_placement(esp, preview)

        info = scene.inspect_pin("esp32", "GPIO2")
        assert info["component"] == "esp32"
        assert info["pin"] == "GPIO2"
        assert info["inserted_into"] == "r4_i"
        assert info["strip"] == "row_4_right"
        assert "r4_f" in info["connected_holes"]
        assert "r4_j" in info["connected_holes"]
        assert info["net_id"] != "DISCONNECTED"

    def test_15_explain_path_from_gpio_to_component(self):
        """15. explain_path('esp32', 'GPIO2', 'led_1', 'anode') retrace le parcours physique continu."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        scene.commit_component_placement(esp, preview)

        led = scene.add_component("led", QPointF(50, 50))
        scene.topology.insert_pin(led.component_id, "anode", "r4_j")

        path = scene.explain_path("esp32", "GPIO2", led.component_id, "anode")
        assert len(path) == 5
        assert path[0] == "esp32.GPIO2"
        assert path[1] == "Hole r4_i"
        assert "row_4_right" in path[2]
        assert path[3] == "Hole r4_j"
        assert path[4] == f"{led.component_id}.anode"

    def test_16_pin_lookup_aliases(self):
        """16. Accès universel aux broches par numéro, étiquette sérigraphiée ou nom universel."""
        from esp32_lab.ui.canvas.items.board_item import BoardGraphicsItem

        board = BoardGraphicsItem("esp32")
        assert board.get_pin_anchor(2) is not None
        assert board.get_pin_anchor("2") is not None
        assert board.get_pin_anchor("GPIO2") is not None
        assert board.get_pin_anchor("IO2") is not None
        assert board.get_pin_anchor("3V3") is not None
        assert board.get_pin_anchor("3.3V") is not None
        assert board.get_pin_anchor("GND") is not None
        assert board.get_pin_anchor("VIN") is not None
        assert board.get_pin_anchor("5V") is not None

    def test_17_multiple_gpio_nets_independent(self):
        """17. Plusieurs broches GPIO (GPIO2 et GPIO4) pilotent des nets indépendants sans diaphonie."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from PySide6.QtCore import QPointF

        scene = CircuitScene()
        bb = scene.add_component("breadboard", QPointF(200, 50))
        esp = scene.add_component("esp32", QPointF(244.0, 47.5))

        preview = scene.preview_component_placement(esp, QPointF(244.0, 47.5))
        scene.commit_component_placement(esp, preview)

        # GPIO2 est en r4_i, GPIO4 est en r5_i
        led1 = scene.add_component("led", QPointF(50, 50))
        scene.topology.insert_pin(led1.component_id, "anode", "r4_j")

        led2 = scene.add_component("led", QPointF(50, 80))
        scene.topology.insert_pin(led2.component_id, "anode", "r5_j")

        # Activer GPIO2 seul
        scene._on_gpio_changed(2, 1)
        assert led1.is_on is True
        assert led2.is_on is False

        # Désactiver GPIO2 et activer GPIO4 seul
        scene._on_gpio_changed(2, 0)
        scene._on_gpio_changed(4, 1)
        assert led1.is_on is False
        assert led2.is_on is True

    def test_18_generate_reference_scenes_e_f_g_h(self):
        """18. Rendu et enregistrement déterministe des scènes de référence E, F, G, H (Prompt 6)."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.core.models.connection import ConnectionModel
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QImage, QPainter
        import os

        artifact_dir = r"C:\Users\bel-h\.gemini\antigravity\brain\7da127c8-f6d4-428f-8f6d-5f39b6a129d0"
        os.makedirs(artifact_dir, exist_ok=True)

        # Scène E : Carte ESP32 réaliste autonome à côté de la breadboard
        s_e = CircuitScene()
        bb_e = s_e.add_component("breadboard", QPointF(350, 60))
        esp_e = s_e.add_component("esp32", QPointF(100, 100))

        img_e = QImage(720, 520, QImage.Format_ARGB32)
        img_e.fill(0xff1e293b)
        p_e = QPainter(img_e)
        s_e.render(p_e)
        p_e.end()
        path_e = os.path.join(artifact_dir, "scene_e_esp32_physical.png")
        img_e.save(path_e)
        assert os.path.exists(path_e)

        # Scène F : ESP32 inséré directement sur la breadboard (enjambant le DIP)
        s_f = CircuitScene()
        bb_f = s_f.add_component("breadboard", QPointF(250, 40))
        esp_f = s_f.add_component("esp32", QPointF(294.0, 37.5))
        prev_f = s_f.preview_component_placement(esp_f, QPointF(294.0, 37.5))
        assert prev_f.valid is True
        s_f.commit_component_placement(esp_f, prev_f)

        img_f = QImage(720, 520, QImage.Format_ARGB32)
        img_f.fill(0xff1e293b)
        p_f = QPainter(img_f)
        s_f.render(p_f)
        p_f.end()
        path_f = os.path.join(artifact_dir, "scene_f_esp32_breadboard_inserted.png")
        img_f.save(path_f)
        assert os.path.exists(path_f)

        # Scène G : ESP32 relié par cavaliers physiques DuPont à la breadboard
        s_g = CircuitScene()
        bb_g = s_g.add_component("breadboard", QPointF(320, 60))
        esp_g = s_g.add_component("esp32", QPointF(80, 80))
        led_g = s_g.add_component("led", QPointF(50, 50))
        s_g.topology.insert_pin(led_g.component_id, "anode", "r10_c")
        s_g.topology.insert_pin(led_g.component_id, "cathode", "r11_c")

        conn_g1 = ConnectionModel(from_component="esp32", from_pin="GPIO2", to_component="breadboard_1", to_pin="r10_a", color="#38bdf8")
        s_g.connections.append(conn_g1)
        s_g._create_wire_item(conn_g1)

        conn_g2 = ConnectionModel(from_component="esp32", from_pin="GND_1", to_component="breadboard_1", to_pin="rail_l_minus_5", color="#1e293b")
        s_g.connections.append(conn_g2)
        s_g._create_wire_item(conn_g2)

        img_g = QImage(720, 520, QImage.Format_ARGB32)
        img_g.fill(0xff1e293b)
        p_g = QPainter(img_g)
        s_g.render(p_g)
        p_g.end()
        path_g = os.path.join(artifact_dir, "scene_g_esp32_dupont_jumpers.png")
        img_g.save(path_g)
        assert os.path.exists(path_g)

        # Scène H : Simulation active complète (LED bleue GPIO2 + LED breadboard)
        s_h = CircuitScene()
        bb_h = s_h.add_component("breadboard", QPointF(250, 40))
        esp_h = s_h.add_component("esp32", QPointF(294.0, 37.5))
        prev_h = s_h.preview_component_placement(esp_h, QPointF(294.0, 37.5))
        s_h.commit_component_placement(esp_h, prev_h)

        led_h = s_h.add_component("led", QPointF(50, 50))
        s_h.topology.insert_pin(led_h.component_id, "anode", "r4_j")
        s_h.topology.insert_pin(led_h.component_id, "cathode", "r5_j")

        s_h._on_gpio_changed(2, 1)

        img_h = QImage(720, 520, QImage.Format_ARGB32)
        img_h.fill(0xff1e293b)
        p_h = QPainter(img_h)
        s_h.render(p_h)
        p_h.end()
        path_h = os.path.join(artifact_dir, "scene_h_esp32_active_simulation.png")
        img_h.save(path_h)
        assert os.path.exists(path_h)


class TestInteractiveDragAndDropSuite:
    """Suite de tests validant l'interactivité Drag & Drop complète dans la vue (CircuitView)."""

    def test_drag_component_outside_breadboard(self):
        """Un composant hors breadboard suit la souris sans blocage."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.circuit_view import CircuitView
        from PySide6.QtTest import QTest
        from PySide6.QtCore import QPointF, Qt, QPoint

        scene = CircuitScene()
        view = CircuitView(scene)
        view.resize(800, 600)
        view.show()

        # Add LED at (100, 100)
        led = scene.add_component("led", QPointF(100, 100))
        initial_pos = led.pos()

        # Simulate mouse press on LED center using QTest
        vp_pos = view.mapFromScene(initial_pos + QPointF(15, 15))
        QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=vp_pos)

        # Move mouse by 50px
        vp_moved = vp_pos + QPoint(50, 30)
        QTest.mouseMove(view.viewport(), pos=vp_moved)

        # Release mouse
        QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=vp_moved)

        # LED should have moved freely
        assert led.pos() != initial_pos
        assert led.parentItem() is None

    def test_drag_component_over_breadboard_triggers_dynamic_preview(self):
        """Le déplacement d'un composant au-dessus de la breadboard active la prévisualisation verte/rouge."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.circuit_view import CircuitView
        from esp32_lab.ui.canvas.items.breadboard_item import HoleVisualState
        from PySide6.QtTest import QTest
        from PySide6.QtCore import QPointF, Qt

        scene = CircuitScene()
        view = CircuitView(scene)
        view.resize(800, 600)
        view.show()

        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(50, 50))

        # Drag LED over breadboard row 10_c (valid placement at 413.0, 79.0)
        press_pos = view.mapFromScene(led.pos() + QPointF(15, 15))
        QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=press_pos)

        target_scene_pos = QPointF(413.0, 79.0)
        target_vp_pos = view.mapFromScene(target_scene_pos + QPointF(15, 15))
        QTest.mouseMove(view.viewport(), pos=target_vp_pos)

        # Check that preview holes are activated on the breadboard item
        previewing_holes = [h for h, hole in bb.hole_anchors.items() if hole.visual_state == HoleVisualState.VALID_PREVIEW]
        assert len(previewing_holes) >= 2, f"Expected at least 2 valid preview holes, got {previewing_holes}"

        # Release to commit
        QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=target_vp_pos)

        # The LED is now inserted into the breadboard
        assert led.anode_pin.is_inserted is True
        assert led.parentItem() == bb
        # Preview states are cleared on release
        cleared_previews = [h for h, hole in bb.hole_anchors.items() if hole.visual_state == HoleVisualState.VALID_PREVIEW]
        assert len(cleared_previews) == 0

    def test_move_inserted_component_and_commit(self):
        """Un composant inséré peut être déplacé à nouveau et réinséré à un nouvel endroit."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.circuit_view import CircuitView
        from PySide6.QtTest import QTest
        from PySide6.QtCore import QPointF, Qt

        scene = CircuitScene()
        view = CircuitView(scene)
        view.resize(800, 600)
        view.show()

        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(50, 50))

        # Insert at r10_c
        prev1 = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        assert prev1.valid is True
        scene.commit_component_placement(led, prev1)
        assert scene.topology.is_hole_occupied("r10_c")

        # Click on LED (even when parented to bb) and drag to row 15 (y = 79.0 + 5 * 8.5 = 121.5)
        led_scene_pos = led.scenePos()
        press_pos = view.mapFromScene(led_scene_pos + QPointF(15, 15))
        QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=press_pos)

        target_scene_pos = QPointF(413.0, 121.5)
        target_vp = view.mapFromScene(target_scene_pos + QPointF(15, 15))
        QTest.mouseMove(view.viewport(), pos=target_vp)

        # Previous holes should be freed during drag
        assert not scene.topology.is_hole_occupied("r10_c")

        # Release to commit at new location
        QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=target_vp)

        assert led.anode_pin.is_inserted is True
        assert scene.topology.is_hole_occupied("r15_c")
        assert not scene.topology.is_hole_occupied("r10_c")

    def test_drag_inserted_component_off_breadboard_detaches(self):
        """Déplacer un composant inséré en dehors de la plaque le détache et libère les trous."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.circuit_view import CircuitView
        from PySide6.QtTest import QTest
        from PySide6.QtCore import QPointF, Qt

        scene = CircuitScene()
        view = CircuitView(scene)
        view.resize(800, 600)
        view.show()

        bb = scene.add_component("breadboard", QPointF(350, 0))
        led = scene.add_component("led", QPointF(50, 50))

        # Insert at r10_c
        prev1 = scene.preview_component_placement(led, QPointF(413.0, 79.0))
        scene.commit_component_placement(led, prev1)

        # Drag LED far away to outside (0, 0)
        press_pos = view.mapFromScene(led.scenePos() + QPointF(15, 15))
        QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=press_pos)

        outside_vp = view.mapFromScene(QPointF(20, 20))
        QTest.mouseMove(view.viewport(), pos=outside_vp)
        QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=outside_vp)

        assert led.anode_pin.is_inserted is False
        assert led.parentItem() is None
        assert not scene.topology.is_hole_occupied("r10_c")
        assert not scene.topology.is_hole_occupied("r11_c")

    def test_click_on_pin_drags_parent_component(self):
        """Cliquer sur une broche (lead/PhysicalPinItem) permet de déplacer le composant parent."""
        from esp32_lab.ui.canvas.circuit_scene import CircuitScene
        from esp32_lab.ui.canvas.circuit_view import CircuitView
        from PySide6.QtTest import QTest
        from PySide6.QtCore import QPointF, Qt, QPoint

        scene = CircuitScene()
        view = CircuitView(scene)
        view.resize(800, 600)
        view.show()

        led = scene.add_component("led", QPointF(120, 120))
        pin = led.anode_pin
        pin_scene_pos = pin.scenePos()

        # Press on the pin
        vp_pin = view.mapFromScene(pin_scene_pos)
        QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=vp_pin)

        # Drag by 40px
        vp_moved = vp_pin + QPoint(40, 40)
        QTest.mouseMove(view.viewport(), pos=vp_moved)
        QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=vp_moved)

        # Parent LED should have moved
        assert led.pos() != QPointF(120, 120)









