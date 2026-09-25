import pytest
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.w25q import W25QxxModel
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

def setup_w25q(engine, dev_id="flash1", variant="W25Q32"):
    spi = sim_machine.SPI(1, sck=18, mosi=23, miso=19)
    flash = W25QxxModel(dev_id, variant=variant)
    engine.models[dev_id] = flash
    
    engine.resolver.add_connection("esp32", "GPIO18", dev_id, "sck")
    engine.resolver.add_connection("esp32", "GPIO23", dev_id, "mosi")
    engine.resolver.add_connection("esp32", "GPIO19", dev_id, "miso")
    engine.resolver.add_connection("esp32", "GPIO5", dev_id, "cs")
    engine.trigger_update()
    
    engine.gpio_manager.configure(5, sim_machine.Pin.OUT)
    engine.gpio_manager.write(5, 1)
    
    return spi, flash

def test_w25q_jedec_id(engine):
    spi, flash = setup_w25q(engine, variant="W25Q32")
    
    engine.gpio_manager.write(5, 0)
    tx = bytearray([0x9F, 0x00, 0x00, 0x00])
    rx = bytearray(4)
    spi.write_readinto(tx, rx)
    engine.gpio_manager.write(5, 1)
    
    assert rx[1:] == b'\xEF\x40\x16'

def test_w25q_write_enable(engine):
    spi, flash = setup_w25q(engine)
    
    engine.gpio_manager.write(5, 0)
    spi.write(bytearray([0x06]))
    engine.gpio_manager.write(5, 1)
    
    assert flash.wel == True
    
    # Read status
    engine.gpio_manager.write(5, 0)
    tx = bytearray([0x05, 0x00])
    rx = bytearray(2)
    spi.write_readinto(tx, rx)
    engine.gpio_manager.write(5, 1)
    assert rx[1] == 0x02
    
    # Write Disable
    engine.gpio_manager.write(5, 0)
    spi.write(bytearray([0x04]))
    engine.gpio_manager.write(5, 1)
    assert flash.wel == False

def test_w25q_page_program(engine):
    spi, flash = setup_w25q(engine)
    
    addr = 0x001000
    data = b'HELLO ESP32 LAB'
    
    # WEL required
    engine.gpio_manager.write(5, 0)
    spi.write(bytearray([0x06]))
    engine.gpio_manager.write(5, 1)
    
    # Page Program
    engine.gpio_manager.write(5, 0)
    tx = bytearray([0x02, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF])
    tx.extend(data)
    spi.write(tx)
    engine.gpio_manager.write(5, 1)
    
    assert flash.wel == False # WEL clears after program
    
    # Read Data
    engine.gpio_manager.write(5, 0)
    tx_read = bytearray([0x03, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF])
    tx_read.extend(bytearray(len(data)))
    rx = bytearray(len(tx_read))
    spi.write_readinto(tx_read, rx)
    engine.gpio_manager.write(5, 1)
    
    assert bytes(rx[4:]) == data
    
    # Fast Read
    engine.gpio_manager.write(5, 0)
    tx_fast = bytearray([0x0B, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF, 0x00]) # 1 dummy byte
    tx_fast.extend(bytearray(len(data)))
    rx_fast = bytearray(len(tx_fast))
    spi.write_readinto(tx_fast, rx_fast)
    engine.gpio_manager.write(5, 1)
    
    assert bytes(rx_fast[5:]) == data

def test_w25q_nor_behavior_and_erase(engine):
    spi, flash = setup_w25q(engine)
    addr = 0x002000
    
    def program(data):
        engine.gpio_manager.write(5, 0)
        spi.write(bytearray([0x06])) # WEL
        engine.gpio_manager.write(5, 1)
        engine.gpio_manager.write(5, 0)
        tx = bytearray([0x02, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF])
        tx.extend(data)
        spi.write(tx)
        engine.gpio_manager.write(5, 1)
        
    def read(length):
        engine.gpio_manager.write(5, 0)
        tx = bytearray([0x03, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF])
        tx.extend(bytearray(length))
        rx = bytearray(len(tx))
        spi.write_readinto(tx, rx)
        engine.gpio_manager.write(5, 1)
        return rx[4:]
        
    program(b'\xFF')
    assert read(1) == b'\xFF'
    program(b'\xF0')
    assert read(1) == b'\xF0'
    program(b'\x0F')
    assert read(1) == b'\x00' # 1->0 behavior, 0xF0 & 0x0F = 0x00
    
    # Sector Erase
    engine.gpio_manager.write(5, 0)
    spi.write(bytearray([0x06])) # WEL
    engine.gpio_manager.write(5, 1)
    
    engine.gpio_manager.write(5, 0)
    tx = bytearray([0x20, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF])
    spi.write(tx)
    engine.gpio_manager.write(5, 1)
    
    assert read(1) == b'\xFF'

def test_w25q_multiple_devices(engine):
    spi = sim_machine.SPI(1, sck=18, mosi=23, miso=19)
    flashA = W25QxxModel("flashA", variant="W25Q32")
    flashB = W25QxxModel("flashB", variant="W25Q64")
    engine.models["flashA"] = flashA
    engine.models["flashB"] = flashB
    
    for dev_id in ["flashA", "flashB"]:
        engine.resolver.add_connection("esp32", "GPIO18", dev_id, "sck")
        engine.resolver.add_connection("esp32", "GPIO23", dev_id, "mosi")
        engine.resolver.add_connection("esp32", "GPIO19", dev_id, "miso")
        
    engine.resolver.add_connection("esp32", "GPIO5", "flashA", "cs")
    engine.resolver.add_connection("esp32", "GPIO17", "flashB", "cs")
    engine.trigger_update()
    
    engine.gpio_manager.configure(5, sim_machine.Pin.OUT)
    engine.gpio_manager.configure(17, sim_machine.Pin.OUT)
    engine.gpio_manager.write(5, 1)
    engine.gpio_manager.write(17, 1)
    
    # JEDEC A
    engine.gpio_manager.write(5, 0)
    rx = bytearray(4)
    spi.write_readinto(bytearray([0x9F, 0, 0, 0]), rx)
    engine.gpio_manager.write(5, 1)
    assert rx[1:] == b'\xEF\x40\x16'
    
    # JEDEC B
    engine.gpio_manager.write(17, 0)
    rx = bytearray(4)
    spi.write_readinto(bytearray([0x9F, 0, 0, 0]), rx)
    engine.gpio_manager.write(17, 1)
    assert rx[1:] == b'\xEF\x40\x17'
    
def test_w25q_cs_conflict(engine):
    spi = sim_machine.SPI(1, sck=18, mosi=23, miso=19)
    flashA = W25QxxModel("flashA")
    flashB = W25QxxModel("flashB")
    engine.models["flashA"] = flashA
    engine.models["flashB"] = flashB
    
    for dev_id in ["flashA", "flashB"]:
        engine.resolver.add_connection("esp32", "GPIO18", dev_id, "sck")
        engine.resolver.add_connection("esp32", "GPIO23", dev_id, "mosi")
        engine.resolver.add_connection("esp32", "GPIO19", dev_id, "miso")
        engine.resolver.add_connection("esp32", "GPIO5", dev_id, "cs")
    engine.trigger_update()
    
    engine.gpio_manager.configure(5, sim_machine.Pin.OUT)
    engine.gpio_manager.write(5, 0)
    
    with pytest.raises(SPICSConflictError):
        spi.write(bytearray([0x9F]))
