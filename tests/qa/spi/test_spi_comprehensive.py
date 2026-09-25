import pytest
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.spi_device import GenericSPIDevice
from esp32_lab.simulator.spi import SPICSConflictError

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

def test_spi_creation_and_api(engine):
    spi = sim_machine.SPI(1, sck=sim_machine.Pin(18), mosi=sim_machine.Pin(23), miso=sim_machine.Pin(19))
    assert 1 in engine.spi_manager.buses
    bus = engine.spi_manager.buses[1]
    assert bus.sck_gpio == "GPIO18"
    assert bus.mosi_gpio == "GPIO23"
    assert bus.miso_gpio == "GPIO19"
    
    spi.deinit()
    assert 1 not in engine.spi_manager.buses

def test_spi_generic_device_transaction(engine):
    spi = sim_machine.SPI(1, sck=sim_machine.Pin(18), mosi=sim_machine.Pin(23), miso=sim_machine.Pin(19))
    dev = GenericSPIDevice("spi_dev_1")
    engine.models["spi_dev_1"] = dev
    
    # Connect SCK, MOSI, MISO, CS
    engine.resolver.add_connection("esp32", "GPIO18", "spi_dev_1", "sck")
    engine.resolver.add_connection("esp32", "GPIO23", "spi_dev_1", "mosi")
    engine.resolver.add_connection("esp32", "GPIO19", "spi_dev_1", "miso")
    engine.resolver.add_connection("esp32", "GPIO5", "spi_dev_1", "cs")
    engine.trigger_update()
    
    # Not selected yet (floating / HIGH)
    rx = spi.read(3, write=0x9F)
    assert rx == b'\xFF\xFF\xFF'
    
    # Select device (Active LOW)
    engine.gpio_manager.configure(5, sim_machine.Pin.OUT)
    engine.gpio_manager.write(5, 0) # Drive LOW
    
    # Try JEDEC ID command
    tx = bytearray([0x9F, 0x00, 0x00, 0x00])
    rx = bytearray(4)
    spi.write_readinto(tx, rx)
    
    assert rx == b'\x00\xEF\x40\x18'
    
    # Deselect
    engine.gpio_manager.write(5, 1) # Drive HIGH
    rx = bytearray(4)
    spi.write_readinto(tx, rx)
    assert rx == b'\xFF\xFF\xFF\xFF'

def test_spi_multiple_devices(engine):
    spi = sim_machine.SPI(1, sck=18, mosi=23, miso=19)
    
    devA = GenericSPIDevice("devA")
    devB = GenericSPIDevice("devB")
    engine.models["devA"] = devA
    engine.models["devB"] = devB
    
    # Connect both to SPI bus
    for dev_id in ["devA", "devB"]:
        engine.resolver.add_connection("esp32", "GPIO18", dev_id, "sck")
        engine.resolver.add_connection("esp32", "GPIO23", dev_id, "mosi")
        engine.resolver.add_connection("esp32", "GPIO19", dev_id, "miso")
        
    # CS A = GPIO5, CS B = GPIO17
    engine.resolver.add_connection("esp32", "GPIO5", "devA", "cs")
    engine.resolver.add_connection("esp32", "GPIO17", "devB", "cs")
    engine.trigger_update()
    
    engine.gpio_manager.configure(5, sim_machine.Pin.OUT)
    engine.gpio_manager.configure(17, sim_machine.Pin.OUT)
    engine.gpio_manager.write(5, 1)
    engine.gpio_manager.write(17, 1)
    
    # Select A
    engine.gpio_manager.write(5, 0)
    tx = bytearray([0x00, 0x00])
    rx = bytearray(2)
    spi.write_readinto(tx, rx)
    assert rx == b'\x00\x42'
    
    # Select B
    engine.gpio_manager.write(5, 1)
    engine.gpio_manager.write(17, 0)
    
    tx = bytearray([0x9F, 0x00, 0x00, 0x00])
    rx = bytearray(4)
    spi.write_readinto(tx, rx)
    assert rx == b'\x00\xEF\x40\x18'

def test_spi_cs_conflict(engine):
    spi = sim_machine.SPI(1, sck=18, mosi=23, miso=19)
    
    devA = GenericSPIDevice("devA")
    devB = GenericSPIDevice("devB")
    engine.models["devA"] = devA
    engine.models["devB"] = devB
    
    # Both connected to same SPI pins
    for dev_id in ["devA", "devB"]:
        engine.resolver.add_connection("esp32", "GPIO18", dev_id, "sck")
        engine.resolver.add_connection("esp32", "GPIO23", dev_id, "mosi")
        engine.resolver.add_connection("esp32", "GPIO19", dev_id, "miso")
        # BOTH connected to SAME CS pin!
        engine.resolver.add_connection("esp32", "GPIO5", dev_id, "cs")
        
    engine.trigger_update()
    
    engine.gpio_manager.configure(5, sim_machine.Pin.OUT)
    engine.gpio_manager.write(5, 0) # Select both
    
    with pytest.raises(SPICSConflictError):
        spi.read(1)

def test_spi_hot_disconnect(engine):
    spi = sim_machine.SPI(1, sck=18, mosi=23, miso=19)
    dev = GenericSPIDevice("spi_dev_1")
    engine.models["spi_dev_1"] = dev
    
    engine.resolver.add_connection("esp32", "GPIO18", "spi_dev_1", "sck")
    engine.resolver.add_connection("esp32", "GPIO23", "spi_dev_1", "mosi")
    engine.resolver.add_connection("esp32", "GPIO19", "spi_dev_1", "miso")
    engine.resolver.add_connection("esp32", "GPIO5", "spi_dev_1", "cs")
    engine.trigger_update()
    
    engine.gpio_manager.configure(5, sim_machine.Pin.OUT)
    engine.gpio_manager.write(5, 0) # LOW
    
    assert spi.read(2, write=0x00) == b'\x00\x42'
    
    # Disconnect MISO
    engine.resolver = ElectricalNetResolver()
    engine.resolver.add_connection("esp32", "GPIO18", "spi_dev_1", "sck")
    engine.resolver.add_connection("esp32", "GPIO23", "spi_dev_1", "mosi")
    engine.resolver.add_connection("esp32", "GPIO5", "spi_dev_1", "cs")
    engine.trigger_update()
    
    # Device should not respond
    assert spi.read(2, write=0x00) == b'\xFF\xFF'
    
    # Reconnect
    engine.resolver.add_connection("esp32", "GPIO19", "spi_dev_1", "miso")
    engine.trigger_update()
    assert spi.read(2, write=0x00) == b'\x00\x42'
