import pytest
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.models.board import create_default_esp32_wroom
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.i2c import I2CAddressConflictError
from esp32_lab.simulator.devices.i2c_device import GenericI2CDevice

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

def test_i2c_pin_validation(engine):
    # Valid
    scl = sim_machine.Pin(22)
    sda = sim_machine.Pin(21)
    i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
    
    # Conflict
    with pytest.raises(ValueError, match="I2C_CONFLICT_PIN"):
        sim_machine.I2C(1, scl=scl, sda=scl, freq=400000)
        
    # Unsupported (Pin 34 is INPUT_ONLY)
    invalid_scl = sim_machine.Pin(34)
    with pytest.raises(ValueError, match="I2C_UNSUPPORTED_PIN"):
        sim_machine.I2C(2, scl=invalid_scl, sda=sda, freq=400000)

def test_i2c_scan_no_devices(engine):
    scl = sim_machine.Pin(22)
    sda = sim_machine.Pin(21)
    i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
    
    assert i2c.scan() == []

def test_i2c_scan_one_device(engine):
    scl = sim_machine.Pin(22)
    sda = sim_machine.Pin(21)
    i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
    
    dev = GenericI2CDevice("dev_1", 0x48)
    engine.models["dev_1"] = dev
    
    # Connect
    engine.resolver.add_connection("esp32", "GPIO22", "dev_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "dev_1", "sda")
    engine.trigger_update()
    
    assert i2c.scan() == [0x48]

def test_i2c_read_write(engine):
    scl = sim_machine.Pin(22)
    sda = sim_machine.Pin(21)
    i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
    
    dev = GenericI2CDevice("dev_1", 0x48)
    engine.models["dev_1"] = dev
    engine.resolver.add_connection("esp32", "GPIO22", "dev_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "dev_1", "sda")
    engine.trigger_update()
    
    # Write to memory address 0x10
    i2c.writeto_mem(0x48, 0x10, b'\xAB')
    
    # Read back
    res = i2c.readfrom_mem(0x48, 0x10, 1)
    assert res == b'\xAB'
    
    # Write without memaddr (first byte is register address)
    i2c.writeto(0x48, b'\x11\xCD')
    res2 = i2c.readfrom_mem(0x48, 0x11, 1)
    assert res2 == b'\xCD'
    
def test_i2c_address_conflict(engine):
    scl = sim_machine.Pin(22)
    sda = sim_machine.Pin(21)
    i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
    
    dev1 = GenericI2CDevice("dev_1", 0x48)
    dev2 = GenericI2CDevice("dev_2", 0x48)
    engine.models["dev_1"] = dev1
    engine.models["dev_2"] = dev2
    
    engine.resolver.add_connection("esp32", "GPIO22", "dev_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "dev_1", "sda")
    
    engine.resolver.add_connection("esp32", "GPIO22", "dev_2", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "dev_2", "sda")
    engine.trigger_update()
    
    with pytest.raises(I2CAddressConflictError):
        i2c.scan()
        
    with pytest.raises(I2CAddressConflictError):
        i2c.writeto(0x48, b'\x00')

def test_i2c_hot_disconnect(engine):
    scl = sim_machine.Pin(22)
    sda = sim_machine.Pin(21)
    i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
    
    dev = GenericI2CDevice("dev_1", 0x48)
    engine.models["dev_1"] = dev
    
    # Connect SDA and SCL
    engine.resolver.add_connection("esp32", "GPIO22", "dev_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "dev_1", "sda")
    engine.trigger_update()
    assert i2c.scan() == [0x48]
    
    # Disconnect SDA
    engine.resolver = ElectricalNetResolver()
    engine.resolver.add_connection("esp32", "GPIO22", "dev_1", "scl")
    engine.trigger_update()
    
    assert i2c.scan() == []
    
    with pytest.raises(OSError, match="ENODEV"):
        i2c.writeto(0x48, b'\x00')

def test_i2c_isolated_buses(engine):
    scl0 = sim_machine.Pin(22)
    sda0 = sim_machine.Pin(21)
    i2c0 = sim_machine.I2C(0, scl=scl0, sda=sda0, freq=400000)
    
    scl1 = sim_machine.Pin(19)
    sda1 = sim_machine.Pin(18)
    i2c1 = sim_machine.I2C(1, scl=scl1, sda=sda1, freq=400000)
    
    dev1 = GenericI2CDevice("dev_1", 0x48)
    dev2 = GenericI2CDevice("dev_2", 0x68)
    engine.models["dev_1"] = dev1
    engine.models["dev_2"] = dev2
    
    # Connect dev1 to I2C0
    engine.resolver.add_connection("esp32", "GPIO22", "dev_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "dev_1", "sda")
    
    # Connect dev2 to I2C1
    engine.resolver.add_connection("esp32", "GPIO19", "dev_2", "scl")
    engine.resolver.add_connection("esp32", "GPIO18", "dev_2", "sda")
    
    engine.trigger_update()
    
    assert i2c0.scan() == [0x48]
    assert i2c1.scan() == [0x68]
