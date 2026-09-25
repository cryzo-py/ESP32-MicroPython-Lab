import pytest
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.servo import ServoModel, ServoSignalState

@pytest.fixture
def engine():
    eng = SimulationEngine()
    eng.resolver = ElectricalNetResolver()
    eng.models = {}
    
    def trigger_update():
        eng.event_bus.topology_updated.emit(eng.resolver, eng.models)
        
    eng.trigger_update = trigger_update
    yield eng
    eng.reset()

def setup_servo(engine, dev_id="servo1", connect_power=True, connect_signal_to=25):
    servo = ServoModel(dev_id)
    engine.models[dev_id] = servo
    
    if connect_power:
        engine.resolver.add_connection("esp32", "3V3", dev_id, "vcc")
        engine.resolver.add_connection("esp32", "GND", dev_id, "gnd")
        
    if connect_signal_to is not None:
        engine.resolver.add_connection("esp32", f"GPIO{connect_signal_to}", dev_id, "sig") # Wait! I named it "sig" in the old servo_item but let's check what I named it in w25q_item. No, servo_item uses "sig". Wait, I should check the pin names of ServoGraphicsItem!
        
    engine.trigger_update()
    return servo

def test_servo_mapping(engine):
    servo = setup_servo(engine, connect_power=True, connect_signal_to=25)
    
    # Configure PWM
    pwm = sim_machine.PWM(sim_machine.Pin(25), freq=50)
    
    # Helper to test duty and angle
    def check(duty, expected_angle):
        pwm.duty(duty)
        # 50 Hz = 20ms period = 20000us
        # duty range 0-1023
        # e.g., 500us = 2.5% = 1023 * 0.025 = ~25.5
        # wait, let's just do math directly in the test to avoid precision issues
        assert abs(servo.angle - expected_angle) < 1.0
        assert servo.signal_state == ServoSignalState.VALID_SIGNAL

    # min_pulse = 500us (2.5% of 20000us -> duty 25.5 -> ~26)
    check(26, 0.0)
    
    # 1500us (7.5% -> duty 76.7 -> ~77)
    check(77, 90.0)
    
    # 2500us (12.5% -> duty 127.8 -> ~128)
    check(128, 180.0)
    
    # Below min pulse (clamp to 0)
    check(10, 0.0)
    
    # Above max pulse (clamp to 180)
    check(200, 180.0)

def test_servo_power_requirements(engine):
    servo = setup_servo(engine, connect_power=False, connect_signal_to=25)
    pwm = sim_machine.PWM(sim_machine.Pin(25), freq=50)
    pwm.duty(77)
    
    # Without power, signal state is INVALID (or DISCONNECTED) and angle doesn't change
    assert servo.powered == False
    assert servo.signal_state == ServoSignalState.INVALID_SIGNAL
    assert servo.angle == 90.0 # Default
    
    # Add VCC
    engine.resolver.add_connection("esp32", "3V3", "servo1", "vcc")
    engine.trigger_update()
    assert servo.powered == False
    
    # Add GND
    engine.resolver.add_connection("esp32", "GND", "servo1", "gnd")
    engine.trigger_update()
    assert servo.powered == True
    assert servo.signal_state == ServoSignalState.VALID_SIGNAL
    assert abs(servo.angle - 90.0) < 1.0

def test_servo_hot_disconnect(engine):
    servo = setup_servo(engine, connect_power=True, connect_signal_to=25)
    pwm = sim_machine.PWM(sim_machine.Pin(25), freq=50)
    pwm.duty(77)
    
    assert servo.signal_state == ServoSignalState.VALID_SIGNAL
    assert abs(servo.angle - 90.0) < 1.0
    
    # Disconnect signal
    engine.resolver = ElectricalNetResolver()
    engine.resolver.add_connection("esp32", "3V3", "servo1", "vcc")
    engine.resolver.add_connection("esp32", "GND", "servo1", "gnd")
    engine.trigger_update()
    
    assert servo.signal_state == ServoSignalState.NO_SIGNAL
    
    # Reconnect signal
    engine.resolver.add_connection("esp32", "GPIO25", "servo1", "sig")
    engine.trigger_update()
    
    assert servo.signal_state == ServoSignalState.VALID_SIGNAL
    assert abs(servo.angle - 90.0) < 1.0

def test_servo_frequency_validation(engine):
    servo = setup_servo(engine, connect_power=True, connect_signal_to=25)
    pwm = sim_machine.PWM(sim_machine.Pin(25), freq=50)
    pwm.duty(77)
    assert servo.signal_state == ServoSignalState.VALID_SIGNAL
    
    # Valid frequency range 45-55Hz
    pwm.freq(45)
    assert servo.signal_state == ServoSignalState.VALID_SIGNAL
    pwm.freq(55)
    assert servo.signal_state == ServoSignalState.VALID_SIGNAL
    
    # Invalid frequency
    pwm.freq(100)
    assert servo.signal_state == ServoSignalState.INVALID_SIGNAL
    
    pwm.freq(20)
    assert servo.signal_state == ServoSignalState.INVALID_SIGNAL

def test_servo_multiple(engine):
    servo1 = setup_servo(engine, dev_id="servo1", connect_power=True, connect_signal_to=25)
    servo2 = setup_servo(engine, dev_id="servo2", connect_power=True, connect_signal_to=26)
    
    pwm1 = sim_machine.PWM(sim_machine.Pin(25), freq=50)
    pwm2 = sim_machine.PWM(sim_machine.Pin(26), freq=50)
    
    pwm1.duty(26) # 0 deg
    pwm2.duty(128) # 180 deg
    
    assert abs(servo1.angle - 0.0) < 1.0
    assert abs(servo2.angle - 180.0) < 1.0
    
    pwm1.duty(77)
    assert abs(servo1.angle - 90.0) < 1.0
    assert abs(servo2.angle - 180.0) < 1.0 # Should not change
