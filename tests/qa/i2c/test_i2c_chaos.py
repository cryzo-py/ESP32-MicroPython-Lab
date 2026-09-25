import pytest
import random
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.i2c_device import GenericI2CDevice
from esp32_lab.simulator.i2c import I2CAddressConflictError

def test_i2c_chaos():
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
    
    addresses = [0x48, 0x49, 0x68, 0x76]
    
    for i in range(50):
        dev_id = f"dev_{i}"
        models[dev_id] = GenericI2CDevice(dev_id, random.choice(addresses))
        
    for op in range(5000):
        action = random.choice(["connect", "disconnect", "scan", "read", "write", "reset"])
        
        if action == "connect":
            dev_id = random.choice(list(models.keys()))
            pin = random.choice(["sda", "scl"])
            gpio = "GPIO21" if pin == "sda" else "GPIO22"
            eng.resolver.add_connection("esp32", gpio, dev_id, pin)
            eng.trigger_update()
            
        elif action == "disconnect":
            eng.resolver = ElectricalNetResolver()
            # Randomly reconnect some to not leave it completely empty
            for _ in range(10):
                dev_id = random.choice(list(models.keys()))
                eng.resolver.add_connection("esp32", "GPIO22", dev_id, "scl")
                eng.resolver.add_connection("esp32", "GPIO21", dev_id, "sda")
            eng.trigger_update()
            
        elif action == "scan":
            try:
                i2c.scan()
            except I2CAddressConflictError:
                pass
                
        elif action == "write":
            try:
                addr = random.choice(addresses)
                i2c.writeto_mem(addr, 0x10, b'\x42')
            except (OSError, I2CAddressConflictError):
                pass
                
        elif action == "read":
            try:
                addr = random.choice(addresses)
                i2c.readfrom_mem(addr, 0x10, 1)
            except (OSError, I2CAddressConflictError):
                pass
                
        elif action == "reset":
            eng.reset()
            # Need to recreate i2c since engine reset tears down buses
            scl = sim_machine.Pin(22)
            sda = sim_machine.Pin(21)
            i2c = sim_machine.I2C(0, scl=scl, sda=sda, freq=400000)
            
    eng.reset()
