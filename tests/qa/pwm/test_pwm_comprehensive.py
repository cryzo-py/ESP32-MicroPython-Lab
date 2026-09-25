import pytest
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.simulator.modules import machine

class DummyConn:
    def __init__(self, c1, p1, c2, p2):
        self.from_component = c1
        self.from_pin = p1
        self.to_component = c2
        self.to_pin = p2

@pytest.fixture
def env():
    engine = SimulationEngine()
    scene = CircuitScene()
    
    def on_top(resolver, models):
        engine.adc_manager.net_resolver = resolver
        engine.adc_manager.device_models = models
        engine.pwm_manager.net_resolver = resolver
        engine.pwm_manager.device_models = models
        
    engine.event_bus.topology_updated.connect(on_top)
    
    esp32 = scene._create_component_item("esp32", "esp32")
    scene.component_items["esp32"] = esp32
    
    return engine, scene

def test_pwm_api_and_validation(env):
    engine, scene = env
    
    # Valid
    pwm = machine.PWM(machine.Pin(25), freq=1000, duty=512)
    assert pwm.freq() == 1000
    assert pwm.duty() == 512
    
    # Validation errors
    with pytest.raises(ValueError):
        machine.PWM(machine.Pin(34)) # Input only
        
    with pytest.raises(ValueError):
        pwm.duty(2000)
        
    with pytest.raises(ValueError):
        pwm.freq(0)

def test_pwm_topology_propagation(env):
    engine, scene = env
    
    led = scene._create_component_item("led", "led1")
    scene.component_items["led1"] = led
    scene.connections.append(DummyConn("esp32", "GPIO25", "led1", "anode"))
    scene.re_evaluate_topology()
    
    pwm = machine.PWM(machine.Pin(25), freq=1000, duty=512)
    
    assert scene.device_models["led1"].brightness == 512 / 1023.0
    
    pwm.duty(1023)
    assert scene.device_models["led1"].brightness == 1.0
    
    pwm.duty(0)
    assert scene.device_models["led1"].brightness == 0.0

def test_pwm_hot_disconnect(env):
    engine, scene = env
    
    led = scene._create_component_item("led", "led1")
    scene.component_items["led1"] = led
    scene.connections.append(DummyConn("esp32", "GPIO25", "led1", "anode"))
    scene.re_evaluate_topology()
    
    pwm = machine.PWM(machine.Pin(25), freq=1000, duty=512)
    assert scene.device_models["led1"].brightness == 512 / 1023.0
    
    scene.connections.clear()
    scene.re_evaluate_topology()
    
    assert scene.device_models["led1"].brightness == 0.0

def test_adc_plus_pwm(env):
    engine, scene = env
    
    pot = scene._create_component_item("potentiometer", "pot1")
    scene.component_items["pot1"] = pot
    scene.connections.append(DummyConn("pot1", "sig", "esp32", "GPIO34"))
    
    led = scene._create_component_item("led", "led1")
    scene.component_items["led1"] = led
    scene.connections.append(DummyConn("esp32", "GPIO25", "led1", "anode"))
    
    scene.re_evaluate_topology()
    
    adc = machine.ADC(machine.Pin(34))
    pwm = machine.PWM(machine.Pin(25))
    
    scene.device_models["pot1"].position = 0.5
    val = adc.read()
    assert val == 2047
    
    pwm.duty(val // 4)
    assert pwm.duty() == 511
    assert scene.device_models["led1"].brightness == 511 / 1023.0
