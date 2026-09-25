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
    
    # Mock update to event bus (CircuitScene handles it now)
    
    esp32 = scene._create_component_item("esp32", "esp32")
    scene.component_items["esp32"] = esp32
    
    return engine, scene

def test_adc_api(env):
    engine, scene = env
    scene.re_evaluate_topology()
    
    # Valid
    adc = machine.ADC(machine.Pin(34))
    assert adc.read() == 0
    assert adc.read_u16() == 0
    
    # Invalid
    with pytest.raises(ValueError):
        machine.ADC(machine.Pin(16)) # GPIO16 not ADC supported
        
def test_adc_gnd_3v3(env):
    engine, scene = env
    
    scene.connections.append(DummyConn("esp32", "GPIO34", "esp32", "GND"))
    scene.connections.append(DummyConn("esp32", "GPIO35", "esp32", "3V3"))
    scene.re_evaluate_topology()
    
    adc34 = machine.ADC(machine.Pin(34))
    adc35 = machine.ADC(machine.Pin(35))
    
    assert adc34.read() == 0
    assert adc35.read() == 4095
    
def test_adc_potentiometer(env):
    engine, scene = env
    
    pot = scene._create_component_item("potentiometer", "pot1")
    scene.component_items["pot1"] = pot
    scene.connections.append(DummyConn("pot1", "sig", "esp32", "GPIO34"))
    scene.re_evaluate_topology()
    
    adc = machine.ADC(machine.Pin(34))
    
    positions = [0.0, 0.25, 0.5, 0.75, 1.0]
    expected = [0, 1023, 2047, 3071, 4095]
    
    for p, e in zip(positions, expected):
        scene.device_models["pot1"].position = p
        assert adc.read() == e
        
def test_adc_conflict(env):
    engine, scene = env
    
    scene.connections.append(DummyConn("esp32", "GPIO34", "esp32", "GND"))
    scene.connections.append(DummyConn("esp32", "GPIO34", "esp32", "3V3"))
    scene.re_evaluate_topology()
    
    adc = machine.ADC(machine.Pin(34))
    assert adc.read() == 0 # behavior defined as returning 0 on conflict
    
def test_adc_hot_disconnect(env):
    engine, scene = env
    
    scene.connections.append(DummyConn("esp32", "GPIO34", "esp32", "3V3"))
    scene.re_evaluate_topology()
    
    adc = machine.ADC(machine.Pin(34))
    assert adc.read() == 4095
    
    scene.connections.clear()
    scene.re_evaluate_topology()
    
    assert adc.read() == 0 # Floating

def test_adc_two_potentiometers(env):
    engine, scene = env
    
    scene.component_items["pot1"] = scene._create_component_item("potentiometer", "pot1")
    scene.component_items["pot2"] = scene._create_component_item("potentiometer", "pot2")
    
    scene.connections.append(DummyConn("pot1", "sig", "esp32", "GPIO34"))
    scene.connections.append(DummyConn("pot2", "sig", "esp32", "GPIO35"))
    scene.re_evaluate_topology()
    
    scene.device_models["pot1"].position = 0.2
    scene.device_models["pot2"].position = 0.8
    
    adc34 = machine.ADC(machine.Pin(34))
    adc35 = machine.ADC(machine.Pin(35))
    
    assert adc34.read() == int(0.2 * 4095)
    assert adc35.read() == int(0.8 * 4095)
    
    scene.device_models["pot1"].position = 0.4
    assert adc34.read() == int(0.4 * 4095)
    assert adc35.read() == int(0.8 * 4095) # unchanged

def test_adc_reset(env):
    engine, scene = env
    
    scene.connections.append(DummyConn("esp32", "GPIO34", "esp32", "3V3"))
    scene.re_evaluate_topology()
    
    adc = machine.ADC(machine.Pin(34))
    assert adc.read() == 4095
    
    engine.reset()
    scene.clear()
    scene.connections.clear()
    scene.re_evaluate_topology()
    
    assert adc.read() == 0
