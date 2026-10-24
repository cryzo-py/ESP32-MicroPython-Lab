"""
Tests unitaires pour le composant graphique Arduino Uno R3 (Commit 2)
Vérifie la création du composant, les points d'ancrage, les LEDs,
l'intégration avec la scène et les connexions électriques.
"""

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from esp32_lab.ui.canvas.items.arduino_uno_item import ArduinoUnoGraphicsItem
from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.connection import ConnectionModel
from esp32_lab.core.models.component import ComponentModel
from esp32_lab.ui.canvas.items.led_item import LEDGraphicsItem


def test_arduino_uno_graphics_item_instantiation(app):
    uno = ArduinoUnoGraphicsItem(board_id="arduino_uno")
    assert uno.width == 190.0
    assert uno.height == 140.0
    assert uno.board_id == "arduino_uno"
    assert uno.component_id == "arduino_uno"

    # Vérification des broches numériques
    for d in range(14):
        anchor = uno.get_pin_anchor(f"D{d}")
        assert anchor is not None, f"Broche D{d} non trouvée"
        # Test lookup par numéro direct
        assert uno.get_pin_anchor(d) == anchor
        assert uno.get_pin_anchor(str(d)) == anchor

    # Vérification des broches analogiques
    for a in range(6):
        anchor_a = uno.get_pin_anchor(f"A{a}")
        assert anchor_a is not None, f"Broche A{a} non trouvée"

    # Vérification de l'alimentation
    assert uno.get_pin_anchor("5V") is not None
    assert uno.get_pin_anchor("3V3") is not None
    assert uno.get_pin_anchor("GND") is not None
    assert uno.get_pin_anchor("VIN") is not None


def test_arduino_uno_led_states_and_power(app):
    uno = ArduinoUnoGraphicsItem(board_id="arduino_uno")
    assert uno.is_powered is False
    assert uno.d13_led_state is False

    uno.set_powered(True)
    assert uno.is_powered is True

    uno.set_led_state(13, True)
    assert uno.d13_led_state is True

    uno.set_led_state("D13", False)
    assert uno.d13_led_state is False


def test_arduino_uno_paint(app):
    uno = ArduinoUnoGraphicsItem(board_id="arduino_uno")
    uno.set_powered(True)
    uno.set_led_state(13, True)

    pixmap = QPixmap(int(uno.width), int(uno.height))
    painter = QPainter(pixmap)
    uno.paint(painter, None)
    painter.end()
    assert not pixmap.isNull()


def test_circuit_scene_add_arduino_uno(app):
    scene = CircuitScene()
    uno = scene.add_component("arduino_uno", QPointF(100, 100))
    assert isinstance(uno, ArduinoUnoGraphicsItem)
    assert scene.board_item == uno
    assert uno.component_id in scene.component_items


def test_circuit_scene_load_project_with_arduino_uno(app):
    proj = ProjectModel(
        name="Projet Uno Test",
        board_id="arduino_uno",
        components=[],
        connections=[]
    )
    scene = CircuitScene()
    scene.load_project_circuit(proj)
    assert isinstance(scene.board_item, ArduinoUnoGraphicsItem)
    assert scene.board_item.board_id == "arduino_uno"


def test_circuit_scene_wire_from_uno_to_led(app):
    scene = CircuitScene()
    uno = scene.add_component("arduino_uno", QPointF(50, 50))
    led = scene.add_component("led", QPointF(250, 50))

    # Connecter D13 de la Uno à l'anode de la LED
    conn_anode = ConnectionModel(
        from_component="arduino_uno",
        from_pin="D13",
        to_component=led.component_id,
        to_pin="anode"
    )
    scene.connections.append(conn_anode)
    scene._create_wire_item(conn_anode)

    # Fermer le circuit : connecter la cathode à GND_1 de la Uno
    conn_gnd = ConnectionModel(
        from_component="arduino_uno",
        from_pin="GND_1",
        to_component=led.component_id,
        to_pin="cathode"
    )
    scene.connections.append(conn_gnd)
    scene._create_wire_item(conn_gnd)

    # Simuler le passage de D13 à HIGH (1)
    scene._on_gpio_changed(13, 1)
    assert led.is_on is True

    # Simuler le passage de D13 à LOW (0)
    scene._on_gpio_changed(13, 0)
    assert led.is_on is False
