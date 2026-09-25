"""
UART Foundation — Implements UART channels and manager for ESP32 MicroPython Lab.

Architecture:
    machine.UART
        ↓
    UARTManager (owned by SimulationEngine)
        ↓
    UARTChannel
        ↓
    ElectricalNetResolver
        ↓
    UARTTerminalModel (or other connected devices)

Provides hardware-accurate routing where bytes are sent physically over
the breadboard logic rather than direct abstract connections.
"""

import collections
import threading
from typing import Optional, Dict

from .gpio import GPIOMode


class UARTChannel:
    """
    Represents a single hardware UART peripheral (e.g. UART1 or UART2).
    Maintains TX/RX configuration and IO buffers.
    """
    def __init__(self, uart_id: int):
        self.id = uart_id
        self.baudrate: int = 115200
        self.bits: int = 8
        self.parity: Optional[int] = None
        self.stop: int = 1
        self.timeout: int = 0
        self.timeout_char: int = 0
        
        self.tx_pin: Optional[int] = None
        self.rx_pin: Optional[int] = None
        
        self.rx_buffer: collections.deque[bytes] = collections.deque()
        self.rx_buffer_size_limit: int = 1024
        
        self._lock = threading.Lock()

    def configure(self, baudrate: int, bits: int, parity: Optional[int], stop: int,
                  timeout: int, timeout_char: int, tx: int, rx: int):
        # Validate settings
        if baudrate <= 0:
            raise ValueError(f"Invalid baudrate: {baudrate}")
        if bits not in (7, 8, 9):
            raise ValueError(f"Invalid bits: {bits}")
        if parity not in (None, 0, 1):
            raise ValueError(f"Invalid parity: {parity}")
        if stop not in (1, 2):
            raise ValueError(f"Invalid stop bits: {stop}")
            
        with self._lock:
            self.baudrate = baudrate
            self.bits = bits
            self.parity = parity
            self.stop = stop
            self.timeout = timeout
            self.timeout_char = timeout_char
            self.tx_pin = tx
            self.rx_pin = rx
            self.rx_buffer.clear()

    def receive_bytes(self, data: bytes):
        """Called by ElectricalNetResolver / Physical layer when bytes arrive at RX."""
        with self._lock:
            for b in data:
                if len(self.rx_buffer) < self.rx_buffer_size_limit:
                    self.rx_buffer.append(bytes([b]))

    def read(self, nbytes: Optional[int] = None) -> Optional[bytes]:
        with self._lock:
            if not self.rx_buffer:
                return None
            if nbytes is None or nbytes >= len(self.rx_buffer):
                res = b"".join(self.rx_buffer)
                self.rx_buffer.clear()
                return res
            
            res = b"".join(self.rx_buffer.popleft() for _ in range(nbytes))
            return res

    def readinto(self, buf: bytearray, nbytes: Optional[int] = None) -> Optional[int]:
        data = self.read(nbytes if nbytes is not None else len(buf))
        if not data:
            return None
        length = min(len(data), len(buf))
        buf[:length] = data[:length]
        return length

    def readline(self) -> Optional[bytes]:
        with self._lock:
            if not self.rx_buffer:
                return None
                
            idx = -1
            for i, b in enumerate(self.rx_buffer):
                if b == b'\n':
                    idx = i
                    break
                    
            if idx == -1:
                return None
                
            res = b"".join(self.rx_buffer.popleft() for _ in range(idx + 1))
            return res

    def any(self) -> int:
        with self._lock:
            return len(self.rx_buffer)

    def reset(self):
        with self._lock:
            self.rx_buffer.clear()
            self.tx_pin = None
            self.rx_pin = None


class UARTManager:
    """
    Manages all UART channels for a single SimulationEngine.
    Handles data transmission across the physical network.
    """
    def __init__(self, gpio_manager):
        self.gpio_manager = gpio_manager
        self.net_resolver = None
        self.device_models = {}
        
        # ESP32 has UART0, UART1, UART2
        self.channels: Dict[int, UARTChannel] = {
            0: UARTChannel(0),
            1: UARTChannel(1),
            2: UARTChannel(2)
        }
        self._lock = threading.Lock()

    def init_uart(self, uart_id: int, baudrate: int, bits: int, parity: Optional[int], stop: int,
                  timeout: int, timeout_char: int, tx: int, rx: int):
        if uart_id not in self.channels:
            raise ValueError(f"Invalid UART ID: {uart_id}")
            
        # Validate pins against board profile
        from ..core.models.board import create_default_esp32_wroom, PinType
        board = create_default_esp32_wroom()
        
        tx_def = board.get_pin(tx)
        rx_def = board.get_pin(rx)
        
        if not tx_def or tx_def.pin_type in (PinType.POWER, PinType.GROUND):
            raise ValueError(f"TX pin {tx} is invalid or is a power pin")
        if tx_def.pin_type == PinType.INPUT_ONLY:
            raise ValueError(f"TX pin {tx} is input-only")
            
        if not rx_def or rx_def.pin_type in (PinType.POWER, PinType.GROUND):
            raise ValueError(f"RX pin {rx} is invalid or is a power pin")

        # In a real ESP32, initializing UART claims the GPIOs. We'll set their modes.
        self.gpio_manager.configure(tx, GPIOMode.OUT)
        self.gpio_manager.configure(rx, GPIOMode.IN)

        channel = self.channels[uart_id]
        channel.configure(baudrate, bits, parity, stop, timeout, timeout_char, tx, rx)

    def deinit_uart(self, uart_id: int):
        if uart_id not in self.channels:
            raise ValueError(f"Invalid UART ID: {uart_id}")
        self.channels[uart_id].reset()

    def write(self, uart_id: int, data: bytes) -> Optional[int]:
        """
        Sends data from the specified UART channel's TX pin, routing it
        through the ElectricalNetResolver to any connected RX pins.
        """
        if uart_id not in self.channels:
            raise ValueError(f"Invalid UART ID: {uart_id}")
            
        channel = self.channels[uart_id]
        tx_pin = channel.tx_pin
        
        if tx_pin is None:
            # UART initialized without TX/RX or deinited
            return None
            
        if self.net_resolver is None:
            return len(data)  # Nowhere to send, bytes blackholed logically

        # Resolve electrical connections
        connected = self.net_resolver.get_connected_pins("esp32", f"GPIO{tx_pin}")
        
        for dev_id, pin_id in connected:
            if dev_id == "esp32":
                # ESP32 loopback: if this GPIO is configured as RX for another UART
                if pin_id.startswith("GPIO"):
                    target_gpio = int(pin_id[4:])
                    # Deliver to any UART channel listening on this RX pin
                    for ch in self.channels.values():
                        if ch.rx_pin == target_gpio:
                            ch.receive_bytes(data)
            else:
                # Deliver to external device models (e.g. UART Terminal)
                dev = self.device_models.get(dev_id)
                if dev and hasattr(dev, "on_uart_rx"):
                    dev.on_uart_rx(pin_id, data)
                    
        return len(data)

    def get_channel(self, uart_id: int) -> UARTChannel:
        if uart_id not in self.channels:
            raise ValueError(f"Invalid UART ID: {uart_id}")
        return self.channels[uart_id]

    def reset(self):
        with self._lock:
            for ch in self.channels.values():
                ch.reset()
