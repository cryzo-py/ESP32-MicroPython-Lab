"""
Tests pour le moteur de simulation et le GPIOManager
"""

import time
from PySide6.QtWidgets import QApplication
import pytest

from esp32_lab.simulator.gpio import GPIOManager, GPIOMode
from esp32_lab.simulator.engine import SimulationEngine


def test_gpio_manager():
    mgr = GPIOManager()
    events = []
    mgr.add_listener(lambda p, v: events.append((p, v)))

    mgr.configure(2, GPIOMode.OUT)
    assert mgr.read(2) == 0

    mgr.write(2, 1)
    assert mgr.read(2) == 1
    assert len(events) == 1
    assert events[0] == (2, 1)

    mgr.write(2, 0)
    assert mgr.read(2) == 0
    assert len(events) == 2
    assert events[1] == (2, 0)


def test_simulation_engine_script(app):
    engine = SimulationEngine()
    
    received_output = []
    engine.event_bus.serial_data_received.connect(lambda s: received_output.append(s))
    
    code = """
from machine import Pin
led = Pin(2, Pin.OUT)
led.value(1)
print("TEST_OK")
"""
    engine.start(code)
    
    # Laisser tourner un bref instant pour que le thread finisse
    deadline = time.time() + 2.0
    while engine.is_running() and time.time() < deadline:
        app.processEvents()
        time.sleep(0.05)
        
    engine.stop()
    
    assert engine.gpio_manager.read(2) == 1
    joined_output = "".join(received_output)
    assert "TEST_OK" in joined_output


def test_simulation_engine_stop_infinite_loop(app):
    engine = SimulationEngine()
    
    code = """
from time import sleep
while True:
    sleep(0.05)
"""
    engine.start(code)
    assert engine.is_running() is True
    
    time.sleep(0.1)
    engine.stop()
    
    deadline = time.time() + 1.0
    while engine.is_running() and time.time() < deadline:
        app.processEvents()
        time.sleep(0.05)
        
    assert engine.is_running() is False
