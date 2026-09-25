import pytest
import random
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.devices.servo import ServoModel, ServoSignalState

def test_servo_chaos():
    random.seed(42)
    eng = SimulationEngine()
    resolver = ElectricalNetResolver()
    models = {}
    
    def trigger_update():
        eng.event_bus.topology_updated.emit(eng.resolver, eng.models)
        
    eng.trigger_update = trigger_update
    eng.resolver = resolver
    eng.models = models
    
    for i in range(5):
        dev_id = f"servo_{i}"
        models[dev_id] = ServoModel(dev_id)
        
    for op in range(5000):
        action = random.choice([
            "connect", "disconnect", "pwm_duty", "pwm_freq", "reset", "power_on", "power_off"
        ])
        
        if action == "connect":
            dev_id = random.choice(list(models.keys()))
            pin = random.choice(["vcc", "gnd", "sig"])
            if pin == "sig": gpio = random.choice(["GPIO25", "GPIO26", "GPIO27"])
            elif pin == "vcc": gpio = "3V3"
            else: gpio = "GND"
            eng.resolver.add_connection("esp32", gpio, dev_id, pin)
            eng.trigger_update()
            
        elif action == "disconnect":
            eng.resolver = ElectricalNetResolver()
            # Randomly reconnect some
            for _ in range(5):
                dev_id = random.choice(list(models.keys()))
                eng.resolver.add_connection("esp32", "3V3", dev_id, "vcc")
                eng.resolver.add_connection("esp32", "GND", dev_id, "gnd")
                eng.resolver.add_connection("esp32", random.choice(["GPIO25", "GPIO26", "GPIO27"]), dev_id, "sig")
            eng.trigger_update()
            
        elif action == "pwm_duty":
            gpio = random.choice([25, 26, 27])
            pwm = sim_machine.PWM(sim_machine.Pin(gpio), freq=50)
            pwm.duty(random.randint(0, 1023))
            
        elif action == "pwm_freq":
            gpio = random.choice([25, 26, 27])
            try:
                pwm = sim_machine.PWM(sim_machine.Pin(gpio), freq=random.choice([40, 50, 60]))
            except ValueError:
                pass
                
        elif action == "power_on":
            for dev_id in models.keys():
                eng.resolver.add_connection("esp32", "3V3", dev_id, "vcc")
                eng.resolver.add_connection("esp32", "GND", dev_id, "gnd")
            eng.trigger_update()
            
        elif action == "power_off":
            eng.resolver = ElectricalNetResolver()
            eng.trigger_update()
            
        elif action == "reset":
            eng.reset()
            # We must redefine PWMs since they are deinit
            
    eng.reset()
