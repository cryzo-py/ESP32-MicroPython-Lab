import pytest
import random
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.ssd1306 import SSD1306Model
from esp32_lab.simulator.devices.bme280 import BME280Model
from esp32_lab.simulator.i2c import I2CAddressConflictError

def test_ssd1306_chaos():
    random.seed(42)
    eng = SimulationEngine()
    resolver = ElectricalNetResolver()
    models = {}
    
    def trigger_update():
        eng.event_bus.topology_updated.emit(eng.resolver, eng.models)
        
    eng.trigger_update = trigger_update
    eng.resolver = resolver
    eng.models = models
    
    scl = sim_machine.Pin(22)
    sda = sim_machine.Pin(21)
    i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
    
    addresses = [0x3C, 0x3D, 0x76]
    
    for i in range(10):
        dev_id = f"oled_{i}"
        models[dev_id] = SSD1306Model(dev_id, address=random.choice([0x3C, 0x3D]))
        bme_id = f"bme_{i}"
        models[bme_id] = BME280Model(bme_id, address=0x76)
        
    for op in range(5000):
        action = random.choice(["connect", "disconnect", "write_cmd", "write_data", "reset"])
        
        if action == "connect":
            dev_id = random.choice(list(models.keys()))
            pin = random.choice(["sda", "scl"])
            gpio = "GPIO21" if pin == "sda" else "GPIO22"
            eng.resolver.add_connection("esp32", gpio, dev_id, pin)
            eng.trigger_update()
            
        elif action == "disconnect":
            eng.resolver = ElectricalNetResolver()
            for _ in range(5):
                dev_id = random.choice(list(models.keys()))
                eng.resolver.add_connection("esp32", "GPIO22", dev_id, "scl")
                eng.resolver.add_connection("esp32", "GPIO21", dev_id, "sda")
            eng.trigger_update()
            
        elif action == "write_cmd":
            try:
                addr = random.choice(addresses)
                reg = 0x00
                val = random.choice([0xAE, 0xAF, 0xA6, 0xA7, 0x20, 0x21, 0x22, 0x81])
                i2c.writeto_mem(addr, reg, bytes([val]))
            except (OSError, I2CAddressConflictError):
                pass
                
        elif action == "write_data":
            try:
                addr = random.choice(addresses)
                reg = 0x40
                length = random.randint(1, 128)
                buf = bytes([random.randint(0, 255) for _ in range(length)])
                i2c.writeto_mem(addr, reg, buf)
            except (OSError, I2CAddressConflictError):
                pass
                
        elif action == "reset":
            eng.reset()
            scl = sim_machine.Pin(22)
            sda = sim_machine.Pin(21)
            i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
            
    eng.reset()
