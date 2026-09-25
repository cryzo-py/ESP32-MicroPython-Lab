import pytest
import random
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.spi_device import GenericSPIDevice
from esp32_lab.simulator.spi import SPICSConflictError

def test_spi_chaos():
    random.seed(42)
    eng = SimulationEngine()
    resolver = ElectricalNetResolver()
    models = {}
    
    def trigger_update():
        eng.event_bus.topology_updated.emit(eng.resolver, eng.models)
        
    eng.trigger_update = trigger_update
    eng.resolver = resolver
    eng.models = models
    
    spi = sim_machine.SPI(1, sck=sim_machine.Pin(18), mosi=sim_machine.Pin(23), miso=sim_machine.Pin(19))
    
    for i in range(5):
        dev_id = f"spi_dev_{i}"
        models[dev_id] = GenericSPIDevice(dev_id)
        
    for op in range(5000):
        action = random.choice(["connect", "disconnect", "cs_low", "cs_high", "transfer", "reset"])
        
        if action == "connect":
            dev_id = random.choice(list(models.keys()))
            pin = random.choice(["sck", "mosi", "miso", "cs"])
            if pin == "sck": gpio = "GPIO18"
            elif pin == "mosi": gpio = "GPIO23"
            elif pin == "miso": gpio = "GPIO19"
            else: gpio = random.choice(["GPIO5", "GPIO17"])
            eng.resolver.add_connection("esp32", gpio, dev_id, pin)
            eng.trigger_update()
            
        elif action == "disconnect":
            eng.resolver = ElectricalNetResolver()
            for _ in range(5):
                dev_id = random.choice(list(models.keys()))
                eng.resolver.add_connection("esp32", "GPIO18", dev_id, "sck")
                eng.resolver.add_connection("esp32", "GPIO23", dev_id, "mosi")
                eng.resolver.add_connection("esp32", "GPIO19", dev_id, "miso")
            eng.trigger_update()
            
        elif action == "cs_low":
            gpio = random.choice([5, 17])
            eng.gpio_manager.configure(gpio, sim_machine.Pin.OUT)
            eng.gpio_manager.write(gpio, 0)
            
        elif action == "cs_high":
            gpio = random.choice([5, 17])
            eng.gpio_manager.configure(gpio, sim_machine.Pin.OUT)
            eng.gpio_manager.write(gpio, 1)
            
        elif action == "transfer":
            try:
                cmd = random.choice([0x9F, 0x00, 0xFF])
                tx = bytearray([cmd, 0, 0, 0])
                rx = bytearray(4)
                spi.write_readinto(tx, rx)
            except SPICSConflictError:
                pass
                
        elif action == "reset":
            eng.reset()
            spi = sim_machine.SPI(1, sck=sim_machine.Pin(18), mosi=sim_machine.Pin(23), miso=sim_machine.Pin(19))
            
    eng.reset()

