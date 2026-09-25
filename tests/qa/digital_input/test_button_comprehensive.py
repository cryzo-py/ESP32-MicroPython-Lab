import pytest
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.simulator.modules import machine
from esp32_lab.core.models.connection import ConnectionModel

@pytest.fixture
def env():
    engine = SimulationEngine()
    scene = CircuitScene()
    
    def on_top(resolver, models):
        engine.adc_manager.net_resolver = resolver
        engine.adc_manager.device_models = models
        engine.pwm_manager.net_resolver = resolver
        engine.pwm_manager.device_models = models
        engine.gpio_manager.net_resolver = resolver
        engine.gpio_manager.device_models = models
        
    engine.event_bus.topology_updated.connect(on_top)
    
    esp32 = scene._create_component_item("esp32", "esp32")
    scene.component_items["esp32"] = esp32
    return engine, scene

def test_pin_in_pull_up(env):
    engine, scene = env
    
    btn = scene._create_component_item("button", "btn1")
    scene.component_items["btn1"] = btn
    
    # Connect pin1 to GPIO27, pin3 to GND (Wait, internal connections: 1a(pin1)-1b(pin2), 2a(pin3)-2b(pin4))
    scene.connections.append(ConnectionModel(from_component="btn1", from_pin="pin1", to_component="esp32", to_pin="GPIO27"))
    scene.connections.append(ConnectionModel(from_component="btn1", from_pin="pin3", to_component="esp32", to_pin="GND.1"))
    scene.re_evaluate_topology()
    
    button = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
    
    # Released -> should be 1 (Pull-up)
    assert button.value() == 1
    
    # Pressed -> should be 0 (GND)
    scene.device_models["btn1"].pressed = True
    scene.re_evaluate_topology()
    assert button.value() == 0
    
    # Released -> should be 1
    scene.device_models["btn1"].pressed = False
    scene.re_evaluate_topology()
    assert button.value() == 1

def test_pin_in_pull_down(env):
    engine, scene = env
    btn = scene._create_component_item("button", "btn1")
    scene.component_items["btn1"] = btn
    
    scene.connections.append(ConnectionModel(from_component="btn1", from_pin="pin1", to_component="esp32", to_pin="GPIO27"))
    scene.connections.append(ConnectionModel(from_component="btn1", from_pin="pin3", to_component="esp32", to_pin="3V3"))
    scene.re_evaluate_topology()
    
    button = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_DOWN)
    
    # Released -> should be 0
    assert button.value() == 0
    
    # Pressed -> should be 1 (3V3)
    scene.device_models["btn1"].pressed = True
    scene.re_evaluate_topology()
    assert button.value() == 1

def test_pin_in_floating(env):
    engine, scene = env
    button = machine.Pin(27, machine.Pin.IN) # No pull
    assert button.value() == 0 # Default floating behavior documented

def test_conflict(env):
    engine, scene = env
    
    scene.connections.append(ConnectionModel(from_component="esp32", from_pin="GPIO27", to_component="esp32", to_pin="GND.1"))
    scene.connections.append(ConnectionModel(from_component="esp32", from_pin="GPIO27", to_component="esp32", to_pin="3V3"))
    scene.re_evaluate_topology()
    
    button = machine.Pin(27, machine.Pin.IN)
    assert button.value() == 0 # Conflict defaults to 0
    
def test_hot_disconnect(env):
    engine, scene = env
    btn = scene._create_component_item("button", "btn1")
    scene.component_items["btn1"] = btn
    
    conn1 = ConnectionModel(from_component="btn1", from_pin="pin1", to_component="esp32", to_pin="GPIO27")
    conn2 = ConnectionModel(from_component="btn1", from_pin="pin3", to_component="esp32", to_pin="GND.1")
    scene.connections.extend([conn1, conn2])
    scene.re_evaluate_topology()
    
    button = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
    scene.device_models["btn1"].pressed = True
    scene.re_evaluate_topology()
    assert button.value() == 0
    
    # Disconnect GND
    scene.connections.remove(conn2)
    scene.re_evaluate_topology()
    
    # Should revert to Pull-up
    assert button.value() == 1

def test_multiple_buttons(env):
    engine, scene = env
    btn1 = scene._create_component_item("button", "btn1")
    btn2 = scene._create_component_item("button", "btn2")
    scene.component_items["btn1"] = btn1
    scene.component_items["btn2"] = btn2
    
    scene.connections.append(ConnectionModel(from_component="btn1", from_pin="pin1", to_component="esp32", to_pin="GPIO27"))
    scene.connections.append(ConnectionModel(from_component="btn1", from_pin="pin3", to_component="esp32", to_pin="GND.1"))
    
    scene.connections.append(ConnectionModel(from_component="btn2", from_pin="pin1", to_component="esp32", to_pin="GPIO26"))
    scene.connections.append(ConnectionModel(from_component="btn2", from_pin="pin3", to_component="esp32", to_pin="GND.2"))
    scene.re_evaluate_topology()
    
    b1 = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
    b2 = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
    
    scene.device_models["btn1"].pressed = True
    scene.re_evaluate_topology()
    
    assert b1.value() == 0
    assert b2.value() == 1
    
    scene.device_models["btn1"].pressed = False
    scene.device_models["btn2"].pressed = True
    scene.re_evaluate_topology()
    
    assert b1.value() == 1
    assert b2.value() == 0

def test_adc_button_pwm(env):
    engine, scene = env
    pot = scene._create_component_item("potentiometer", "pot1")
    scene.component_items["pot1"] = pot
    scene.connections.append(ConnectionModel(from_component="pot1", from_pin="sig", to_component="esp32", to_pin="GPIO34"))
    scene.connections.append(ConnectionModel(from_component="pot1", from_pin="vcc", to_component="esp32", to_pin="3V3"))
    
    btn = scene._create_component_item("button", "btn1")
    scene.component_items["btn1"] = btn
    scene.connections.append(ConnectionModel(from_component="btn1", from_pin="pin1", to_component="esp32", to_pin="GPIO27"))
    scene.connections.append(ConnectionModel(from_component="btn1", from_pin="pin3", to_component="esp32", to_pin="GND.1"))
    
    led = scene._create_component_item("led", "led1")
    scene.component_items["led1"] = led
    scene.connections.append(ConnectionModel(from_component="led1", from_pin="anode", to_component="esp32", to_pin="GPIO25"))
    
    scene.re_evaluate_topology()
    
    adc = machine.ADC(machine.Pin(34))
    button = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
    pwm = machine.PWM(machine.Pin(25))
    
    # Initial state
    scene.device_models["pot1"].position = 0.5
    assert adc.read() == 2047
    assert button.value() == 1
    
    pwm.duty(512)
    assert scene.device_models["led1"].brightness == 512 / 1023.0
    
    # Press button
    scene.device_models["btn1"].pressed = True
    scene.re_evaluate_topology()
    assert button.value() == 0
    
    # Button press shouldn't affect ADC or PWM directly unless the user script does it
    assert adc.read() == 2047
    assert scene.device_models["led1"].brightness == 512 / 1023.0
