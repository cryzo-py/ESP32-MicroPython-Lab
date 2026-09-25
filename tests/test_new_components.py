"""
Tests unitaires pour les nouveaux composants électroniques :
LDR, LED RGB 4 broches, Capteur PIR HC-SR501, Joystick KY-023, Interrupteur SPDT.
"""

import pytest
from PySide6.QtCore import QPointF
from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.ui.canvas.items.ldr_item import LDRGraphicsItem
from esp32_lab.ui.canvas.items.rgb_led_item import RGBLEDGraphicsItem
from esp32_lab.ui.canvas.items.pir_item import PIRGraphicsItem
from esp32_lab.ui.canvas.items.joystick_item import JoystickGraphicsItem
from esp32_lab.ui.canvas.items.switch_item import SlideSwitchGraphicsItem
from esp32_lab.ui.panels.properties_panel import PropertiesPanelWidget


def test_ldr_component(app):
    """Vérifie le comportement de la photorésistance (LDR)."""
    ldr = LDRGraphicsItem("ldr_1", lux=300.0)
    assert ldr.component_id == "ldr_1"
    assert ldr.lux == 300.0
    # Obscurité = haute résistance, Plein soleil = basse résistance
    ldr.lux = 1000.0
    r_sun = ldr.resistance_value
    ldr.lux = 10.0
    r_dark = ldr.resistance_value
    assert r_dark > r_sun
    assert len(ldr.childItems()) == 2 # 2 broches physiques


def test_rgb_led_component(app):
    """Vérifie la LED RGB 4 broches (synthèse additive et PWM)."""
    rgb = RGBLEDGraphicsItem("rgb_1", r=255, g=0, b=0)
    assert rgb.component_id == "rgb_1"
    assert rgb.val_r == 255
    assert rgb.val_g == 0
    assert rgb.val_b == 0
    assert len(rgb.childItems()) == 4 # R, GND, G, B

    # Changement de couleur direct
    rgb.set_color_rgb(0, 255, 128)
    assert rgb.val_g == 255
    assert rgb.val_b == 128

    # Contrôle PWM (0-1023)
    rgb.set_pwm("r", 1023)
    assert rgb.val_r == 255
    rgb.set_pwm("r", 0)
    assert rgb.val_r == 0


def test_pir_motion_sensor(app):
    """Vérifie le capteur de mouvement PIR HC-SR501."""
    pir = PIRGraphicsItem("pir_1")
    assert pir.component_id == "pir_1"
    assert not pir.motion_detected
    assert len(pir.childItems()) == 3 # VCC, OUT, GND

    pir.trigger_motion(duration_ms=100)
    assert pir.motion_detected


def test_joystick_component(app):
    """Vérifie le joystick analogique 2 axes KY-023."""
    joy = JoystickGraphicsItem("joy_1", x_val=2048, y_val=2048)
    assert joy.component_id == "joy_1"
    assert joy.x_val == 2048
    assert joy.y_val == 2048
    assert not joy.sw_pressed
    assert len(joy.childItems()) == 5 # GND, VCC, VRx, VRy, SW

    joy.set_position(4095, 0, sw_pressed=True)
    assert joy.x_val == 4095
    assert joy.y_val == 0
    assert joy.sw_pressed


def test_slide_switch_component(app):
    """Vérifie l'interrupteur à glissière SPDT."""
    sw = SlideSwitchGraphicsItem("sw_1", is_on=False)
    assert sw.component_id == "sw_1"
    assert not sw.is_on
    assert len(sw.childItems()) == 3 # Pin1, COM, Pin2

    sw.toggle()
    assert sw.is_on
    sw.toggle()
    assert not sw.is_on


def test_scene_add_all_new_components(app):
    """Vérifie l'ajout des 5 nouveaux composants dans la scène de circuit."""
    scene = CircuitScene()
    
    ldr = scene.add_component("ldr")
    assert isinstance(ldr, LDRGraphicsItem)

    rgb = scene.add_component("rgb_led")
    assert isinstance(rgb, RGBLEDGraphicsItem)

    pir = scene.add_component("pir")
    assert isinstance(pir, PIRGraphicsItem)

    joy = scene.add_component("joystick")
    assert isinstance(joy, JoystickGraphicsItem)

    sw = scene.add_component("switch")
    assert isinstance(sw, SlideSwitchGraphicsItem)

    assert "ldr_1" in scene.component_items
    assert "rgb_led_1" in scene.component_items
    assert "pir_1" in scene.component_items
    assert "joystick_1" in scene.component_items
    assert "switch_1" in scene.component_items


def test_properties_panel_new_components(app):
    """Vérifie l'inspection des 5 nouveaux composants dans le panneau de propriétés."""
    panel = PropertiesPanelWidget()
    
    # LDR
    panel.inspect_component("ldr_1", "ldr", {"lux": 500.0})
    assert panel.current_component_id == "ldr_1"

    # RGB LED
    panel.inspect_component("rgb_1", "rgb_led", {"r": 100, "g": 200, "b": 50})
    assert panel.current_component_id == "rgb_1"

    # PIR
    panel.inspect_component("pir_1", "pir", {"motion_detected": False})
    assert panel.current_component_id == "pir_1"

    # Joystick
    panel.inspect_component("joy_1", "joystick", {"x": 2048, "y": 2048})
    assert panel.current_component_id == "joy_1"

    # Switch
    panel.inspect_component("sw_1", "switch", {"is_on": True})
    assert panel.current_component_id == "sw_1"
