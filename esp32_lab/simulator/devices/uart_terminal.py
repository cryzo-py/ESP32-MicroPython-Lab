"""
Virtual UART Terminal Device Model for ESP32 MicroPython Lab
"""
from typing import Optional, Callable
import collections

class UARTTerminalModel:
    """
    Virtual UART Terminal device.
    Pins:
        - VCC
        - GND
        - TX (Terminal's TX, connects to ESP32 RX)
        - RX (Terminal's RX, connects to ESP32 TX)
    """
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.net_resolver = None
        
        self.rx_buffer = collections.deque()
        self.rx_buffer_limit = 4096
        
        self.on_data_received: Optional[Callable[[bytes], None]] = None
        
        # Injected by engine via EventBus / SimulationEngine
        self._uart_manager = None

    def set_net_resolver(self, resolver):
        self.net_resolver = resolver

    def on_uart_rx(self, pin_id: str, data: bytes):
        """Called by UARTManager when data arrives at a pin of this terminal."""
        if pin_id == "RX":
            # Data received from ESP32
            for b in data:
                if len(self.rx_buffer) < self.rx_buffer_limit:
                    self.rx_buffer.append(bytes([b]))
            
            if self.on_data_received:
                self.on_data_received(data)

    def write_tx(self, data: bytes):
        """
        Called by the UI to inject data into the Terminal's TX pin.
        Routes it to any electrically connected ESP32 RX pins.
        """
        if self.net_resolver is None or self._uart_manager is None:
            return
            
        connected = self.net_resolver.get_connected_pins(self.device_id, "TX")
        for dev_id, pin_id in connected:
            if dev_id == "esp32":
                if pin_id.startswith("GPIO"):
                    target_gpio = int(pin_id[4:])
                    for ch in self._uart_manager.channels.values():
                        if ch.rx_pin == target_gpio:
                            ch.receive_bytes(data)
            else:
                # Terminal to Terminal ? (Edge case, support later if needed)
                pass

    def get_state_dict(self) -> dict:
        return {
            "type": "uart_terminal",
            "buffer_size": len(self.rx_buffer)
        }
        
    def reset(self):
        self.rx_buffer.clear()
        
    @classmethod
    def from_dict(cls, data: dict, device_id: str) -> 'UARTTerminalModel':
        return cls(device_id)

    def to_dict(self) -> dict:
        return {
            "type": "uart_terminal"
        }
