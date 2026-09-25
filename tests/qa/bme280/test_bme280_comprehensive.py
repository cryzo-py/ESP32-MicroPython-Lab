import pytest
import time
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.bme280 import BME280Model
from esp32_lab.simulator.i2c import I2CAddressConflictError

@pytest.fixture
def engine():
    eng = SimulationEngine()
    resolver = ElectricalNetResolver()
    models = {}
    
    def trigger_update():
        eng.event_bus.topology_updated.emit(eng.resolver, eng.models)
        
    eng.trigger_update = trigger_update
    eng.resolver = resolver
    eng.models = models
    
    yield eng
    eng.reset()

def test_bme280_creation(engine):
    bme = BME280Model("bme_1", address=0x76)
    assert bme.address == 0x76
    assert bme.temperature == 24.5
    
    bme2 = BME280Model("bme_2", address=0x77)
    assert bme2.address == 0x77

def test_bme280_chip_id(engine):
    bme = BME280Model("bme_1")
    engine.models["bme_1"] = bme
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.trigger_update()
    
    scl = sim_machine.Pin(22)
    sda = sim_machine.Pin(21)
    i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
    
    chip_id = i2c.readfrom_mem(0x76, 0xD0, 1)
    assert chip_id == b'\x60'

def test_bme280_reset(engine):
    bme = BME280Model("bme_1")
    engine.models["bme_1"] = bme
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    
    # Write some config
    i2c.writeto_mem(0x76, 0xF4, b'\x27')
    assert i2c.readfrom_mem(0x76, 0xF4, 1) == b'\x27'
    
    # Reset
    i2c.writeto_mem(0x76, 0xE0, b'\xB6')
    
    # Verify config is reset to 0
    assert i2c.readfrom_mem(0x76, 0xF4, 1) == b'\x00'

def test_bme280_measurements(engine):
    # Set to a very specific environment
    bme = BME280Model("bme_1", temperature=20.0, pressure=1000.0, humidity=40.0)
    engine.models["bme_1"] = bme
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.trigger_update()
    
    # Emulate the driver directly in Python to ensure our model satisfies the real math
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    
    # We will just verify that the direct method _find_adc_values followed by _compensate_* gives good results
    adc_t, adc_p, adc_h = bme._find_adc_values()
    
    T, t_fine = bme._compensate_T(adc_t)
    assert abs(T - 2000) < 5 # within 0.05 C
    
    P = bme._compensate_P(adc_p, t_fine)
    assert abs(P - 256000) < 256 # within 1 hPa
    
    H = bme._compensate_H(adc_h, t_fine)
    assert abs(H - 40960) < 1024 # within 1 %

def test_bme280_modes(engine):
    bme = BME280Model("bme_1")
    engine.models["bme_1"] = bme
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    
    # SLEEP MODE
    i2c.writeto_mem(0x76, 0xF4, b'\x00')
    assert i2c.readfrom_mem(0x76, 0xF4, 1) == b'\x00'
    
    # FORCED MODE
    i2c.writeto_mem(0x76, 0xF4, b'\x25')
    assert i2c.readfrom_mem(0x76, 0xF4, 1) == b'\x25'
    
    # NORMAL MODE
    i2c.writeto_mem(0x76, 0xF4, b'\x27')
    assert i2c.readfrom_mem(0x76, 0xF4, 1) == b'\x27'

def test_bme280_hot_disconnect(engine):
    bme = BME280Model("bme_1")
    engine.models["bme_1"] = bme
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    assert i2c.readfrom_mem(0x76, 0xD0, 1) == b'\x60'
    
    # Disconnect SDA
    engine.resolver = ElectricalNetResolver()
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.trigger_update()
    
    import pytest
    with pytest.raises(OSError, match="ENODEV"):
        i2c.readfrom_mem(0x76, 0xD0, 1)
        
    # Reconnect
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.trigger_update()
    
    assert i2c.readfrom_mem(0x76, 0xD0, 1) == b'\x60'

def test_multiple_bme280_isolation(engine):
    bme1 = BME280Model("bme_1", address=0x76, temperature=10.0)
    bme2 = BME280Model("bme_2", address=0x77, temperature=40.0)
    engine.models["bme_1"] = bme1
    engine.models["bme_2"] = bme2
    
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.resolver.add_connection("esp32", "GPIO22", "bme_2", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_2", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    devices = i2c.scan()
    assert 0x76 in devices
    assert 0x77 in devices
    
    # Read raw temperature from bme1
    raw1 = i2c.readfrom_mem(0x76, 0xFA, 3)
    raw2 = i2c.readfrom_mem(0x77, 0xFA, 3)
    
    assert raw1 != raw2

def test_bme280_conflict(engine):
    bme1 = BME280Model("bme_1", address=0x76)
    bme2 = BME280Model("bme_2", address=0x76)
    engine.models["bme_1"] = bme1
    engine.models["bme_2"] = bme2
    
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.resolver.add_connection("esp32", "GPIO22", "bme_2", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_2", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    
    import pytest
    with pytest.raises(I2CAddressConflictError):
        i2c.readfrom_mem(0x76, 0xD0, 1)

def test_bme280_lifecycle(engine):
    for i in range(10):
        bme = BME280Model("bme_1")
        engine.models["bme_1"] = bme
        engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
        engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
        engine.trigger_update()
        
        i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
        assert i2c.readfrom_mem(0x76, 0xD0, 1) == b'\x60'
        
        engine.reset()
        engine.models = {}
        engine.resolver = ElectricalNetResolver()
        engine.trigger_update()
