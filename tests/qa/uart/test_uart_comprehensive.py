"""
Comprehensive tests for Phase 5.13 UART Foundation
"""
import pytest
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.uart import UARTManager, UARTChannel
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.simulator.devices.uart_terminal import UARTTerminalModel
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver

@pytest.fixture
def engine():
    eng = SimulationEngine()
    eng.gpio_manager.configure = lambda pin, mode, pull=0: None # mock gpio valid
    return eng

@pytest.fixture
def uart_mgr(engine):
    return engine.uart_manager

class TestUARTManager:
    def test_init_invalid_id(self, uart_mgr):
        with pytest.raises(ValueError):
            uart_mgr.init_uart(99, 115200, 8, None, 1, 0, 0, 17, 16)
            
    def test_init_valid(self, uart_mgr):
        uart_mgr.init_uart(1, 9600, 8, None, 1, 0, 0, 17, 16)
        ch = uart_mgr.get_channel(1)
        assert ch.baudrate == 9600
        assert ch.tx_pin == 17
        assert ch.rx_pin == 16

class TestUARTAPI:
    def test_api_uninitialized(self):
        u = sim_machine.UART(1)
        # Should not crash if not initialized
        assert u.any() == 0
        assert u.read() is None

class TestUARTConfiguration:
    def test_invalid_baudrate(self, uart_mgr):
        with pytest.raises(ValueError):
            uart_mgr.init_uart(1, -1, 8, None, 1, 0, 0, 17, 16)
            
    def test_invalid_bits(self, uart_mgr):
        with pytest.raises(ValueError):
            uart_mgr.init_uart(1, 115200, 10, None, 1, 0, 0, 17, 16)

class TestUARTBuffers:
    def test_buffer_limit(self, uart_mgr):
        uart_mgr.init_uart(1, 115200, 8, None, 1, 0, 0, 17, 16)
        ch = uart_mgr.get_channel(1)
        # fill buffer
        ch.receive_bytes(b"A" * 2000)
        assert len(ch.rx_buffer) == 1024  # limit is 1024
        
class TestUARTReadline:
    def test_readline(self, uart_mgr):
        uart_mgr.init_uart(1, 115200, 8, None, 1, 0, 0, 17, 16)
        ch = uart_mgr.get_channel(1)
        ch.receive_bytes(b"HELLO\nWORLD")
        assert ch.readline() == b"HELLO\n"
        assert ch.read() == b"WORLD"

class TestUARTReadinto:
    def test_readinto(self, uart_mgr):
        uart_mgr.init_uart(1, 115200, 8, None, 1, 0, 0, 17, 16)
        ch = uart_mgr.get_channel(1)
        ch.receive_bytes(b"12345")
        buf = bytearray(3)
        n = ch.readinto(buf)
        assert n == 3
        assert buf == b"123"
        assert ch.read() == b"45"

class TestUARTLifecycle:
    def test_reset_clears_buffer(self, engine, uart_mgr):
        uart_mgr.init_uart(1, 115200, 8, None, 1, 0, 0, 17, 16)
        uart_mgr.get_channel(1).receive_bytes(b"TEST")
        engine.reset()
        assert len(uart_mgr.get_channel(1).rx_buffer) == 0

class TestUARTPhysicalTopology:
    def test_tx_rx_loopback(self, engine, uart_mgr):
        # Setup electrical net
        resolver = ElectricalNetResolver()
        resolver.connections = [(("esp32", "GPIO17"), ("esp32", "GPIO16"))]
        engine.uart_manager.net_resolver = resolver
        
        uart = sim_machine.UART(1, baudrate=115200, tx=17, rx=16)
        uart.write(b"LOOP")
        
        # Bytes should physically route from GPIO17 to GPIO16
        assert uart.any() == 4
        assert uart.read() == b"LOOP"

    def test_uart_terminal(self, engine):
        term = UARTTerminalModel("term_1")
        engine.uart_manager.device_models["term_1"] = term
        term._uart_manager = engine.uart_manager
        
        resolver = ElectricalNetResolver()
        # Connect ESP32 TX (17) to Terminal RX
        # Connect ESP32 RX (16) to Terminal TX
        resolver.connections = [
            (("esp32", "GPIO17"), ("term_1", "RX")),
            (("esp32", "GPIO16"), ("term_1", "TX"))
        ]
        engine.uart_manager.net_resolver = resolver
        term.set_net_resolver(resolver)
        
        uart = sim_machine.UART(1, baudrate=115200, tx=17, rx=16)
        
        # ESP32 -> Terminal
        uart.write(b"HELLO TERMINAL")
        assert b"".join(term.rx_buffer) == b"HELLO TERMINAL"
        
        # Terminal -> ESP32
        term.write_tx(b"HELLO ESP32")
        assert uart.read() == b"HELLO ESP32"

    def test_disconnect(self, engine):
        term = UARTTerminalModel("term_1")
        engine.uart_manager.device_models["term_1"] = term
        term._uart_manager = engine.uart_manager
        
        resolver = ElectricalNetResolver()
        resolver.connections = [(("esp32", "GPIO17"), ("term_1", "RX"))]
        engine.uart_manager.net_resolver = resolver
        
        uart = sim_machine.UART(1, baudrate=115200, tx=17, rx=16)
        uart.write(b"1")
        assert len(term.rx_buffer) == 1
        
        # Disconnect
        resolver.connections = []
        uart.write(b"2")
        assert len(term.rx_buffer) == 1  # No new data
        
        # Reconnect
        resolver.connections = [(("esp32", "GPIO17"), ("term_1", "RX"))]
        uart.write(b"3")
        assert len(term.rx_buffer) == 2  # New data arrived

class TestUARTMultipleChannels:
    def test_multiple_uarts(self, engine):
        resolver = ElectricalNetResolver()
        resolver.connections = [
            (("esp32", "GPIO17"), ("esp32", "GPIO16")),  # UART1 loopback
            (("esp32", "GPIO4"), ("esp32", "GPIO5"))     # UART2 loopback
        ]
        engine.uart_manager.net_resolver = resolver
        
        u1 = sim_machine.UART(1, tx=17, rx=16)
        u2 = sim_machine.UART(2, tx=4, rx=5)
        
        u1.write(b"A")
        u2.write(b"B")
        
        assert u1.read() == b"A"
        assert u2.read() == b"B"
