import sys
import random
import time
sys.path.insert(0, r"D:\Projets\ESP32 Lab")

from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.core.models.connection import ConnectionModel
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])

def test_chaos_integration():
    random.seed(42)
    scene = CircuitScene()
    scene.add_component("esp32")
    
    comp_types = ["led", "button", "potentiometer"]
    
    from esp32_lab.simulator.engine import SimulationEngine
    engine = SimulationEngine()
    
    def on_top(resolver, models):
        engine._on_topology_updated(resolver, models)
        
    engine.event_bus.topology_updated.connect(on_top)
    
    for i in range(5000):
        op = random.choice([
            "ADD", "REMOVE", "MOVE", "CONNECT", "DISCONNECT", 
            "ADC_READ", "PWM_DUTY", "PWM_FREQ", "PIN_VALUE_READ", "PIN_VALUE_WRITE",
            "BUTTON_PRESS", "BUTTON_RELEASE", "POT_MOVE"
        ])
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
            elif op == "ADC_READ":
                pin = random.choice([32, 33, 34, 35])
                engine.adc_manager.configure(pin)
                val = engine.adc_manager.read(pin)
            elif op == "PWM_DUTY":
                pin = random.choice([25, 26, 27])
                engine.pwm_manager.configure(pin)
                engine.pwm_manager.set_duty(pin, random.randint(0, 1023))
            elif op == "PWM_FREQ":
                pin = random.choice([25, 26, 27])
                engine.pwm_manager.configure(pin)
                engine.pwm_manager.set_frequency(pin, random.randint(1, 10000))
            elif op == "PIN_VALUE_READ":
                pin = random.choice([25, 26, 27, 34])
                from esp32_lab.simulator.gpio import GPIOMode, GPIOPull
                engine.gpio_manager.configure(pin, GPIOMode.IN, GPIOPull.PULL_UP)
                val = engine.gpio_manager.read(pin)
            elif op == "PIN_VALUE_WRITE":
                pin = random.choice([25, 26, 27])
                from esp32_lab.simulator.gpio import GPIOMode
                engine.gpio_manager.configure(pin, GPIOMode.OUT)
                engine.gpio_manager.write(pin, random.choice([0, 1]))
            elif op == "BUTTON_PRESS":
                buttons = [k for k in scene.component_items.keys() if "button" in k]
                if buttons:
                    b = buttons[0]
                    item = scene.component_items[b]
                    if hasattr(item, 'model'): item.model.press()
                    elif hasattr(item, 'press'): item.press()
            elif op == "BUTTON_RELEASE":
                buttons = [k for k in scene.component_items.keys() if "button" in k]
                if buttons:
                    b = buttons[0]
                    item = scene.component_items[b]
                    if hasattr(item, 'model'): item.model.release()
                    elif hasattr(item, 'release'): item.release()
            elif op == "POT_MOVE":
                pots = [k for k in scene.component_items.keys() if "potentiometer" in k]
                if pots:
                    p = pots[0]
                    item = scene.component_items[p]
                    if hasattr(item, 'model'): item.model.set_position(random.random())
                    elif hasattr(item, 'set_position'): item.set_position(random.random())

            if i % 50 == 0:
                scene.re_evaluate_topology()
                
        except ValueError as ve:
            # Expected validation errors, ignore
            pass
        except Exception as e:
            assert False, f"Chaos crashed at iteration {i} on op {op}: {e}"
            
    print("Integration chaos test passed 5000 ops.")

if __name__ == "__main__":
    test_chaos_integration()
