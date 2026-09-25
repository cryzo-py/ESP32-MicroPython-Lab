"""
Tests automatisés pour le moteur de vérification des règles électriques (ERC)
"""
import pytest
from esp32_lab.core.erc_checker import ElectricalRulesChecker, ERCSeverity


def test_erc_detects_direct_short_circuit():
    checker = ElectricalRulesChecker()
    components = [
        {"id": "esp32", "type": "esp32"},
    ]
    # Court-circuit franc : 3V3 relié directement à GND_1
    connections = [
        {"from_component": "esp32", "from_pin": "3V3", "to_component": "esp32", "to_pin": "GND_1"}
    ]

    violations = checker.analyze(components, connections)
    assert len(violations) >= 1
    v = violations[0]
    assert v.severity == ERCSeverity.ERROR
    assert "Court-circuit" in v.title
    assert "esp32" in v.component_ids


def test_erc_detects_led_without_resistor():
    checker = ElectricalRulesChecker()
    components = [
        {"id": "esp32", "type": "esp32"},
        {"id": "led_1", "type": "led"},
    ]
    # LED branchée directement entre GPIO2 et GND sans résistance
    connections = [
        {"from_component": "esp32", "from_pin": "GPIO2", "to_component": "led_1", "to_pin": "anode"},
        {"from_component": "led_1", "from_pin": "cathode", "to_component": "esp32", "to_pin": "GND_1"},
    ]

    violations = checker.analyze(components, connections)
    led_violations = [v for v in violations if "LED_NO_RESISTOR" in v.id]
    assert len(led_violations) == 1
    assert led_violations[0].severity == ERCSeverity.WARNING
    assert "led_1" in led_violations[0].component_ids


def test_erc_accepts_led_with_resistor():
    checker = ElectricalRulesChecker()
    components = [
        {"id": "esp32", "type": "esp32"},
        {"id": "r1", "type": "resistor", "properties": {"value": 220}},
        {"id": "led_1", "type": "led"},
    ]
    # ESP32 GPIO2 -> r1 (pin1), r1 (pin2) -> led_1 (anode), led_1 (cathode) -> ESP32 GND
    # r1 crée une liaison physique mais pas un court-circuit
    connections = [
        {"from_component": "esp32", "from_pin": "GPIO2", "to_component": "r1", "to_pin": "pin1"},
        {"from_component": "r1", "from_pin": "pin2", "to_component": "led_1", "to_pin": "anode"},
        {"from_component": "led_1", "from_pin": "cathode", "to_component": "esp32", "to_pin": "GND_1"},
    ]

    violations = checker.analyze(components, connections)
    led_violations = [v for v in violations if "LED_NO_RESISTOR" in v.id]
    assert len(led_violations) == 0


def test_erc_detects_output_collision():
    checker = ElectricalRulesChecker()
    components = [
        {"id": "esp32", "type": "esp32"},
    ]
    # Deux GPIO reliées ensemble
    connections = [
        {"from_component": "esp32", "from_pin": "GPIO18", "to_component": "esp32", "to_pin": "GPIO19"}
    ]
    # Simulation active : GPIO18 = OUT (1), GPIO19 = OUT (0)
    gpio_states = {
        18: {"mode": "OUT", "value": 1},
        19: {"mode": "OUT", "value": 0},
    }

    violations = checker.analyze(components, connections, gpio_states=gpio_states)
    collision_violations = [v for v in violations if "OUTPUT_COLLISION" in v.id]
    assert len(collision_violations) == 1
    assert collision_violations[0].severity == ERCSeverity.ERROR


def test_snap_engine_rejects_pins_on_same_strip():
    from PySide6.QtCore import QPointF
    from esp32_lab.core.breadboard_topology import BreadboardTopology
    from esp32_lab.ui.canvas.snap_engine import SnapEngine, PinInfo

    engine = SnapEngine()
    topology = BreadboardTopology()

    # Broches alignées horizontalement sur 8.5px (ex: potentiomètre ou capteur DHT22)
    pins = [
        PinInfo(pin_id="pin1", rel_x=-8.5, rel_y=0.0),
        PinInfo(pin_id="pin2", rel_x=0.0, rel_y=0.0),
        PinInfo(pin_id="pin3", rel_x=8.5, rel_y=0.0),
    ]

    # Si positionné sur la rangée 10 (gauche), toutes les broches tomberaient sur row_10_left
    hole_pos = topology.get_hole_position("r10_c")
    assert hole_pos is not None
    preview = engine.compute_placement_preview(pins, QPointF(hole_pos[0], hole_pos[1]), topology)
    assert not preview.valid
    assert preview.reason == "PINS_IN_SAME_STRIP"

    # En revanche, broches alignées verticalement (comme une LED ou résistance) doivent être valides
    vertical_pins = [
        PinInfo(pin_id="anode", rel_x=0.0, rel_y=-8.5),
        PinInfo(pin_id="cathode", rel_x=0.0, rel_y=0.0),
    ]
    v_preview = engine.compute_placement_preview(vertical_pins, QPointF(hole_pos[0], hole_pos[1]), topology)
    assert v_preview.valid
    assert v_preview.reason is None


def test_all_built_in_examples_pass_erc():
    from PySide6.QtWidgets import QApplication
    _ = QApplication.instance() or QApplication([])
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.examples import get_all_examples
    from esp32_lab.core.erc_checker import ElectricalRulesChecker

    examples = get_all_examples()
    checker = ElectricalRulesChecker()

    for name, proj in examples.items():
        scene = CircuitScene()
        scene.load_project_circuit(proj)
        comps_data = [{'id': c.id, 'type': c.type, 'properties': dict(c.properties)} for c in proj.components]
        conns_data = [{'from_component': c.from_component, 'from_pin': c.from_pin, 'to_component': c.to_component, 'to_pin': c.to_pin} for c in proj.connections]
        violations = checker.analyze(comps_data, conns_data, topology=scene.topology)
        errors = [v for v in violations if v.severity.name == 'ERROR']
        assert len(errors) == 0, f"Exemple '{name}' comporte des erreurs ERC : {[e.message for e in errors]}"

