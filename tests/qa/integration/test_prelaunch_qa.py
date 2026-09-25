import pytest
import time
import tracemalloc
import gc
from PySide6.QtWidgets import QApplication
from esp32_lab.simulator.engine import SimulationEngine

@pytest.fixture
def app_loop():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

@pytest.fixture
def sim_engine(app_loop):
    engine = SimulationEngine()
    yield engine
    engine.stop()

def pump_events(app, duration):
    deadline = time.time() + duration
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)

def test_tc05_infinite_loop(sim_engine, app_loop):
    code = "while True: pass"
    sim_engine.start(code)
    pump_events(app_loop, 0.5)
    assert sim_engine.is_running()
    
    sim_engine.stop()
    pump_events(app_loop, 0.5)
    assert not sim_engine.is_running()

def test_memory_leak(sim_engine, app_loop):
    gc.collect()
    tracemalloc.start()
    
    code = "a = [x for x in range(1000)]"
    for _ in range(50):
        sim_engine.start(code)
        pump_events(app_loop, 0.05)
        sim_engine.stop()
        pump_events(app_loop, 0.01)
        
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    leak_mb = current / (1024 * 1024)
    print(f"Memory leak: {leak_mb:.4f} MB")
    assert leak_mb < 5.0
