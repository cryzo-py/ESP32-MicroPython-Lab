import sys
import random
sys.path.insert(0, r"D:\Projets\ESP32 Lab")

from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.core.models.connection import ConnectionModel
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])

def test_chaos():
    random.seed(42)
    scene = CircuitScene()
    scene.add_component("esp32")
    
    comp_types = ["led", "resistor", "button", "buzzer", "rgb_led", "potentiometer"]
    
    # We need the SimulationEngine to get ADCManager
    from esp32_lab.simulator.engine import SimulationEngine
    engine = SimulationEngine()
    
    # Mock update to event bus (CircuitScene handles it now)
    def on_top(resolver, models):
        engine.adc_manager.net_resolver = resolver
        engine.adc_manager.device_models = models
        
    engine.event_bus.topology_updated.connect(on_top)
    
    for i in range(5000):
        op = random.choice(["ADD", "REMOVE", "MOVE", "CONNECT", "DISCONNECT", "ADC", "PWM_CREATE", "PWM_DUTY"])
        try:
            if op == "ADD":
                ctype = random.choice(comp_types)
                scene.add_component(ctype)
            elif op == "REMOVE":
                keys = list(scene.component_items.keys())
                if keys:
                    k = random.choice(keys)
                    if k != "esp32":
                        item = scene.component_items[k]
                        scene._execute_delete_items([item])
            elif op == "CONNECT":
                keys = list(scene.component_items.keys())
                if len(keys) >= 2:
                    c1, c2 = random.sample(keys, 2)
                    conn = ConnectionModel(c1, "pin1", c2, "pin2")
                    scene.connections.append(conn)
            elif op == "DISCONNECT":
                if scene.connections:
                    c = random.choice(scene.connections)
                    scene.connections.remove(c)
            elif op == "ADC":
                val = engine.adc_manager.read(34)
            elif op == "PWM_CREATE":
                from esp32_lab.simulator.modules import machine
                pwm = machine.PWM(machine.Pin(25))
            elif op == "PWM_DUTY":
                from esp32_lab.simulator.modules import machine
                pwm = machine.PWM(machine.Pin(25))
                pwm.duty(random.randint(0, 1023))
                    
            # Every 100 ops, try to resolve net
            if i % 100 == 0:
                scene.re_evaluate_topology()
                
        except Exception as e:
            print(f"Chaos crashed at iteration {i} on op {op}: {e}")
            return
            
    print("Chaos test finished 5000 ops without crash.")

if __name__ == "__main__":
    test_chaos()
