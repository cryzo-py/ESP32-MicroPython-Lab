"""
Tests unitaires pour les composants avancés (DHT22, SSD1306, Servo, Potentiomètre)
"""

import time
import pytest

from esp32_lab.core.examples import get_all_examples
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules.dht import set_sensor_data


def test_examples_library():
    examples = get_all_examples()
    assert len(examples) >= 6
    assert "blink" in examples
    assert "button_led" in examples
    assert "pot_pwm" in examples
    assert "servo_sweep" in examples
    assert "dht22_weather" in examples
    assert "oled_display" in examples

    for key, proj in examples.items():
        assert proj.name
        assert "main.py" in proj.files
        assert len(proj.components) > 0


def test_dht22_simulation(app):
    engine = SimulationEngine()
    
    # Prérégler les données du capteur sur GPIO 4
    set_sensor_data(4, 28.5, 72.0)
    
    output = []
    engine.event_bus.serial_data_received.connect(lambda s: output.append(s))
    
    code = """
import dht
from machine import Pin

s = dht.DHT22(Pin(4))
s.measure()
t = s.temperature()
h = s.humidity()
print(f"DHT_RESULT:{t}:{h}")
"""
    engine.start(code)
    
    deadline = time.time() + 1.5
    while engine.is_running() and time.time() < deadline:
        app.processEvents()
        time.sleep(0.05)
        
    engine.stop()
    joined = "".join(output)
    assert "DHT_RESULT:28.5:72.0" in joined


def test_potentiometer_and_pwm(app):
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    engine = SimulationEngine()
    scene = CircuitScene()
    
    # Connect pot to GPIO34
    esp32 = scene._create_component_item("esp32", "esp32")
    scene.component_items["esp32"] = esp32
    pot = scene._create_component_item("potentiometer", "pot1")
    scene.component_items["pot1"] = pot
    from esp32_lab.core.models.connection import ConnectionModel
    scene.connections.append(ConnectionModel(from_component="pot1", from_pin="sig", to_component="esp32", to_pin="GPIO34"))
    scene.re_evaluate_topology()
    
    # Set position to ~ 75%
    scene.device_models["pot1"].position = 3072 / 4095.0
    
    def on_top(resolver, models):
        engine.adc_manager.net_resolver = resolver
        engine.adc_manager.device_models = models
        engine.pwm_manager.net_resolver = resolver
        engine.pwm_manager.device_models = models
        
    engine.event_bus.topology_updated.connect(on_top)
    scene.re_evaluate_topology()
    
    print("DEBUG ADC BEFORE:", engine.adc_manager.read(34))
    
    output = []
    engine.event_bus.serial_data_received.connect(lambda s: output.append(s))
    
    code = """
from machine import Pin, ADC, PWM

pot = ADC(Pin(34))
val = pot.read()

servo = PWM(Pin(18), freq=50)
servo.duty(77)

print(f"POT_READ:{val}")
"""
    engine.start(code)
    
    deadline = time.time() + 1.5
    while engine.is_running() and time.time() < deadline:
        app.processEvents()
        time.sleep(0.05)
        
    engine.stop()
    joined = "".join(output)
    assert "POT_READ:3072" in joined


def test_component_rotation_and_wires(app):
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.examples import create_blink_example

    scene = CircuitScene()
    proj = create_blink_example()
    scene.load_project_circuit(proj)

    led_item = scene.component_items.get("led_1")
    assert led_item is not None
    assert led_item.rotation() == 0.0

    # Sélectionner et tourner à 90°
    led_item.setSelected(True)
    scene.rotate_selected_component(90.0)
    assert led_item.rotation() == 90.0

    # Vérifier que les fils ont recalculé leurs extrémités
    wire = scene.wire_items.get("w1")
    assert wire is not None
    assert not wire.path().isEmpty()

