"""
Chaos testing for Phase 5.13 UART Foundation
"""
import pytest
import random
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.simulator.devices.uart_terminal import UARTTerminalModel
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver

def test_uart_chaos():
    eng = SimulationEngine()
    eng.gpio_manager.configure = lambda pin, mode, pull=0: None # mock
    
    term = UARTTerminalModel("term_1")
    eng.uart_manager.device_models["term_1"] = term
    term._uart_manager = eng.uart_manager
    
    resolver = ElectricalNetResolver()
    eng.uart_manager.net_resolver = resolver
    term.set_net_resolver(resolver)
    
    uarts = [
        sim_machine.UART(0, tx=1, rx=3),
        sim_machine.UART(1, tx=17, rx=16),
        sim_machine.UART(2, tx=4, rx=5)
    ]
    
    topology_states = [
        [], # isolated
        [(("esp32", "GPIO17"), ("esp32", "GPIO16"))], # U1 loop
        [(("esp32", "GPIO17"), ("term_1", "RX")), (("esp32", "GPIO16"), ("term_1", "TX"))], # U1 <-> term
        [(("esp32", "GPIO1"), ("term_1", "RX"))], # U0 -> term
        [(("esp32", "GPIO4"), ("term_1", "RX")), (("esp32", "GPIO16"), ("esp32", "GPIO5"))] # mixed
    ]
    
    for _ in range(5000):
        op = random.choice([
            "write", "read", "readinto", "readline", "any", 
            "deinit", "init", "term_write", "change_topology", "reset"
        ])
        
        u = random.choice(uarts)
        
        if op == "write":
            u.write(b"A" * random.randint(1, 50))
        elif op == "read":
            u.read(random.choice([None, 5, 100]))
        elif op == "readinto":
            u.readinto(bytearray(10))
        elif op == "readline":
            u.readline()
        elif op == "any":
            u.any()
        elif op == "deinit":
            u.deinit()
        elif op == "init":
            u.init(tx=random.choice([1, 17, 4]), rx=random.choice([3, 16, 5]))
        elif op == "term_write":
            term.write_tx(b"T" * random.randint(1, 10))
        elif op == "change_topology":
            resolver.connections = random.choice(topology_states)
        elif op == "reset":
            eng.reset()
            # Must recreate UI links
            term._uart_manager = eng.uart_manager
            eng.uart_manager.device_models["term_1"] = term
            eng.uart_manager.net_resolver = resolver
            
    assert True
