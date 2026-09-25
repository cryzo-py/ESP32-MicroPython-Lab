import pytest
import random
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.bme280 import BME280Model
from esp32_lab.simulator.i2c import I2CAddressConflictError

def test_bme280_chaos():
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
    
    addresses = [0x76, 0x77]
    
    for i in range(20):
        dev_id = f"bme_{i}"
        models[dev_id] = BME280Model(dev_id, address=random.choice(addresses))
        
    for op in range(5000):
        action = random.choice(["connect", "disconnect", "read", "write", "reset"])
        
        if action == "connect":
            dev_id = random.choice(list(models.keys()))
            pin = random.choice(["sda", "scl"])
            gpio = "GPIO21" if pin == "sda" else "GPIO22"
            eng.resolver.add_connection("esp32", gpio, dev_id, pin)
            eng.trigger_update()
            
        elif action == "disconnect":
            eng.resolver = ElectricalNetResolver()
            # Randomly reconnect some
            for _ in range(5):
                dev_id = random.choice(list(models.keys()))
                eng.resolver.add_connection("esp32", "GPIO22", dev_id, "scl")
                eng.resolver.add_connection("esp32", "GPIO21", dev_id, "sda")
            eng.trigger_update()
            
        elif action == "write":
            try:
                addr = random.choice(addresses)
                reg = random.choice([0xE0, 0xF2, 0xF4, 0xF5])
                val = random.randint(0, 255)
                i2c.writeto_mem(addr, reg, bytes([val]))
            except (OSError, I2CAddressConflictError):
                pass
                
        elif action == "read":
            try:
                addr = random.choice(addresses)
                reg = random.choice([0xD0, 0xF7, 0x88])
                i2c.readfrom_mem(addr, reg, 8)
            except (OSError, I2CAddressConflictError):
                pass
                
        elif action == "reset":
            eng.reset()
            scl = sim_machine.Pin(22)
            sda = sim_machine.Pin(21)
            i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
            
    eng.reset()
