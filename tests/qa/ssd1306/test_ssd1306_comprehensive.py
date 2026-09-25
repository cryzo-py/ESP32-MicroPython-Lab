import pytest
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.ssd1306 import SSD1306Model
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

def test_ssd1306_creation(engine):
    oled = SSD1306Model("oled_1", address=0x3C, width=128, height=64)
    assert oled.address == 0x3C
    assert len(oled.framebuffer) == 1024
    assert oled.is_on == False

def test_ssd1306_commands(engine):
    oled = SSD1306Model("oled_1")
    engine.models["oled_1"] = oled
    engine.resolver.add_connection("esp32", "GPIO22", "oled_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "oled_1", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    
    # Display ON
    i2c.writeto_mem(0x3C, 0x00, b'\xAF')
    assert oled.is_on == True
    
    # Display OFF
    i2c.writeto_mem(0x3C, 0x00, b'\xAE')
    assert oled.is_on == False
    
    # Invert
    i2c.writeto_mem(0x3C, 0x00, b'\xA7')
    assert oled.inverted == True

def test_ssd1306_framebuffer(engine):
    oled = SSD1306Model("oled_1")
    engine.models["oled_1"] = oled
    engine.resolver.add_connection("esp32", "GPIO22", "oled_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "oled_1", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    
    # Write page address (Page 0)
    i2c.writeto_mem(0x3C, 0x00, b'\x22\x00\x00')
    # Write column address (Col 0)
    i2c.writeto_mem(0x3C, 0x00, b'\x21\x00\x7F')
    
    # Write data (1 byte)
    i2c.writeto_mem(0x3C, 0x40, b'\xFF')
    
    assert oled.framebuffer[0] == 0xFF
    assert oled.framebuffer[1] == 0x00
    
    # The pointer should have auto-incremented based on addressing mode (Page addressing is default)
    assert oled.curr_col == 1

def test_ssd1306_bme280_isolation(engine):
    oled = SSD1306Model("oled_1", address=0x3C)
    bme = BME280Model("bme_1", address=0x76, temperature=20.0)
    engine.models["oled_1"] = oled
    engine.models["bme_1"] = bme
    
    engine.resolver.add_connection("esp32", "GPIO22", "oled_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "oled_1", "sda")
    engine.resolver.add_connection("esp32", "GPIO22", "bme_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "bme_1", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    
    devices = i2c.scan()
    assert 0x3C in devices
    assert 0x76 in devices
    
    # Write to OLED
    i2c.writeto_mem(0x3C, 0x00, b'\xAF')
    assert oled.is_on == True
    
    # Write to BME280
    i2c.writeto_mem(0x76, 0xE0, b'\xB6') # Reset
    assert bme.address == 0x76

def test_ssd1306_hot_disconnect(engine):
    oled = SSD1306Model("oled_1")
    engine.models["oled_1"] = oled
    engine.resolver.add_connection("esp32", "GPIO22", "oled_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "oled_1", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    i2c.writeto_mem(0x3C, 0x00, b'\xAF')
    
    # Disconnect SDA
    engine.resolver = ElectricalNetResolver()
    engine.resolver.add_connection("esp32", "GPIO22", "oled_1", "scl")
    engine.trigger_update()
    
    with pytest.raises(OSError):
        i2c.writeto_mem(0x3C, 0x00, b'\xAF')
        
    # Reconnect
    engine.resolver.add_connection("esp32", "GPIO21", "oled_1", "sda")
    engine.trigger_update()
    
    i2c.writeto_mem(0x3C, 0x00, b'\xAF')

def test_ssd1306_conflict(engine):
    oled1 = SSD1306Model("oled_1", address=0x3C)
    oled2 = SSD1306Model("oled_2", address=0x3C)
    engine.models["oled_1"] = oled1
    engine.models["oled_2"] = oled2
    
    engine.resolver.add_connection("esp32", "GPIO22", "oled_1", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "oled_1", "sda")
    engine.resolver.add_connection("esp32", "GPIO22", "oled_2", "scl")
    engine.resolver.add_connection("esp32", "GPIO21", "oled_2", "sda")
    engine.trigger_update()
    
    i2c = sim_machine.I2C(0, scl=sim_machine.Pin(22), sda=sim_machine.Pin(21), freq=400000)
    
    with pytest.raises(I2CAddressConflictError):
        i2c.writeto_mem(0x3C, 0x00, b'\xAF')
