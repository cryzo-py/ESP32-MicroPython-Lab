from typing import Dict, List, Optional
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver

class SPICSConflictError(Exception):
    pass

class SPIBus:
    def __init__(self, bus_id: int, sck_gpio: int, mosi_gpio: int, miso_gpio: int,
                 freq: int = 1000000, polarity: int = 0, phase: int = 0, firstbit: int = 0):
        self.bus_id = bus_id
        self.sck_gpio = f"GPIO{sck_gpio}"
        self.mosi_gpio = f"GPIO{mosi_gpio}"
        self.miso_gpio = f"GPIO{miso_gpio}"
        self.freq = freq
        self.polarity = polarity
        self.phase = phase
        self.firstbit = firstbit

class SPIManager:
    def __init__(self, gpio_manager=None):
        self.net_resolver: Optional[ElectricalNetResolver] = None
        self.gpio_manager = gpio_manager
        self.device_models: Dict[str, object] = {}
        self.buses: Dict[int, SPIBus] = {}
        
    def reset(self):
        self.buses.clear()
        
    def init_bus(self, bus_id: int, sck: int, mosi: int, miso: int,
                 freq: int = 1000000, polarity: int = 0, phase: int = 0, firstbit: int = 0) -> SPIBus:
        bus = SPIBus(bus_id, sck, mosi, miso, freq, polarity, phase, firstbit)
        self.buses[bus_id] = bus
        return bus
        
    def deinit_bus(self, bus_id: int):
        if bus_id in self.buses:
            del self.buses[bus_id]

    def _get_active_devices(self, bus: SPIBus) -> List[object]:
        if not self.net_resolver:
            return []

        sck_net = self.net_resolver.get_connected_pins("esp32", bus.sck_gpio)
        mosi_net = self.net_resolver.get_connected_pins("esp32", bus.mosi_gpio)
        miso_net = self.net_resolver.get_connected_pins("esp32", bus.miso_gpio)

        active_devices = []

        for dev_id, model in self.device_models.items():
            if not hasattr(model, "spi_transfer"):
                continue

            sck_pin = getattr(model, "spi_sck_pin", "sck")
            if (dev_id, sck_pin) not in sck_net:
                continue

            mosi_pin = getattr(model, "spi_mosi_pin", "mosi")
            if (dev_id, mosi_pin) not in mosi_net:
                continue

            miso_pin = getattr(model, "spi_miso_pin", "miso")
            if (dev_id, miso_pin) not in miso_net:
                continue
                
            cs_pin = getattr(model, "spi_cs_pin", "cs")
            cs_net_pins = self.net_resolver.get_connected_pins(dev_id, cs_pin)
            cs_gpio = None
            for p_cid, p_name in cs_net_pins:
                if p_cid == "esp32" and p_name.startswith("GPIO"):
                    cs_gpio = p_name
                    break
            
            if not cs_gpio or not self.gpio_manager:
                continue

            # Read the logical state of the CS GPIO
            net_state = self.gpio_manager.get_net_state(int(cs_gpio.replace("GPIO", "")))
            
            if net_state.value == 0 and net_state.status != "FLOATING": # Active LOW
                active_devices.append(model)
                
        return active_devices

    def transfer(self, bus_id: int, tx_data: bytes) -> bytes:
        if bus_id not in self.buses:
            raise OSError(f"SPI bus {bus_id} not initialized")
            
        bus = self.buses[bus_id]
        active_devices = self._get_active_devices(bus)
        
        if len(active_devices) > 1:
            raise SPICSConflictError(f"Multiple SPI devices selected on bus {bus_id}")
            
        if not active_devices:
            return bytes([0xFF] * len(tx_data))
            
        device = active_devices[0]
        rx_data = device.spi_transfer(tx_data, bus.polarity, bus.phase)
        
        if rx_data is None:
            rx_data = bytes([0xFF] * len(tx_data))
            
        if len(rx_data) < len(tx_data):
            rx_data += bytes([0xFF] * (len(tx_data) - len(rx_data)))
        elif len(rx_data) > len(tx_data):
            rx_data = rx_data[:len(tx_data)]
            
        return rx_data


