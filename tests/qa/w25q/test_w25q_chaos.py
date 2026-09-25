import pytest
import random
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.w25q import W25QxxModel
from esp32_lab.simulator.spi import SPICSConflictError

def test_w25q_chaos():
    random.seed(42)
    eng = SimulationEngine()
    resolver = ElectricalNetResolver()
    models = {}
    
    def trigger_update():
        eng.event_bus.topology_updated.emit(eng.resolver, eng.models)
        
    eng.trigger_update = trigger_update
    eng.resolver = resolver
    eng.models = models
    
    spi = sim_machine.SPI(1, sck=18, mosi=23, miso=19)
    
    for i in range(5):
        dev_id = f"flash_{i}"
        models[dev_id] = W25QxxModel(dev_id, variant=random.choice(["W25Q32", "W25Q64"]))
        
    for op in range(5000):
        action = random.choice([
            "connect", "disconnect", "cs_low", "cs_high",
            "jedec", "write_enable", "page_program", "read", "erase", "reset"
        ])
        
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
            
        elif action in ["jedec", "write_enable", "page_program", "read", "erase"]:
            try:
                if action == "jedec":
                    tx = bytearray([0x9F, 0, 0, 0])
                elif action == "write_enable":
                    tx = bytearray([0x06])
                elif action == "page_program":
                    addr = random.randint(0, 0x1000)
                    tx = bytearray([0x02, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF, 0xAA, 0xBB])
                elif action == "read":
                    addr = random.randint(0, 0x1000)
                    tx = bytearray([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF, 0, 0])
                elif action == "erase":
                    addr = random.randint(0, 0x1000)
                    tx = bytearray([0x20, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF])
                    
                rx = bytearray(len(tx))
                spi.write_readinto(tx, rx)
            except SPICSConflictError:
                pass
                
        elif action == "reset":
            eng.reset()
            spi = sim_machine.SPI(1, sck=18, mosi=23, miso=19)
            
    eng.reset()
