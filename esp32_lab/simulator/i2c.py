from typing import Dict, List, Optional
from esp32_lab.core.models.board import create_default_esp32_wroom

class I2CAddressConflictError(Exception):
    pass
    
class I2CBusError(Exception):
    pass

class I2CBus:
    def __init__(self, bus_id: int, scl_pin: int, sda_pin: int, freq: int):
        self.bus_id = bus_id
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.freq = freq

class I2CManager:
    def __init__(self):
        self.buses: Dict[int, I2CBus] = {}
        self.net_resolver = None
        self.device_models = {}

    def configure_bus(self, bus_id: int, scl_pin: int, sda_pin: int, freq: int):
        board = create_default_esp32_wroom()
        
        scl_def = board.get_pin(scl_pin)
        sda_def = board.get_pin(sda_pin)
        
        if not scl_def or not sda_def:
            raise ValueError("I2C_INVALID_PIN")
        if not scl_def.supports_i2c or not sda_def.supports_i2c:
            raise ValueError("I2C_UNSUPPORTED_PIN")
        if scl_pin == sda_pin:
            raise ValueError("I2C_CONFLICT_PIN")
            
        self.buses[bus_id] = I2CBus(bus_id, scl_pin, sda_pin, freq)

    def _get_connected_devices(self, bus_id: int) -> List[any]:
        if bus_id not in self.buses:
            raise ValueError("I2C_INVALID_BUS")
        bus = self.buses[bus_id]
        
        if not self.net_resolver:
            return []
            
        try:
            scl_net = self.net_resolver.get_connected_pins("esp32", f"GPIO{bus.scl_pin}")
            sda_net = self.net_resolver.get_connected_pins("esp32", f"GPIO{bus.sda_pin}")
        except Exception:
            return []
            
        devices = []
        for comp_id, model in self.device_models.items():
            if getattr(model, 'is_i2c_device', False):
                sda_pin_name = getattr(model, "sda_pin_name", "sda")
                scl_pin_name = getattr(model, "scl_pin_name", "scl")
                
                scl_connected = any(c == comp_id and p == scl_pin_name for c, p in scl_net)
                sda_connected = any(c == comp_id and p == sda_pin_name for c, p in sda_net)
                
                if scl_connected and sda_connected:
                    devices.append(model)
                    
        return devices

    def scan(self, bus_id: int) -> List[int]:
        devices = self._get_connected_devices(bus_id)
        addresses = set()
        for dev in devices:
            if dev.address in addresses:
                raise I2CAddressConflictError(f"I2C_ADDRESS_CONFLICT: {hex(dev.address)}")
            addresses.add(dev.address)
        return sorted(list(addresses))

    def _get_device_by_addr(self, bus_id: int, addr: int):
        if addr < 0x03 or addr > 0x77:
            raise ValueError(f"I2C_INVALID_ADDRESS: {hex(addr)}")
            
        devices = self._get_connected_devices(bus_id)
        found = [d for d in devices if d.address == addr]
        if len(found) > 1:
            raise I2CAddressConflictError(f"I2C_ADDRESS_CONFLICT: {hex(addr)}")
        if not found:
            raise OSError("[Errno 19] ENODEV")
        return found[0]

    def writeto(self, bus_id: int, addr: int, data: bytes | bytearray) -> int:
        dev = self._get_device_by_addr(bus_id, addr)
        dev.write(data)
        return len(data)

    def readfrom(self, bus_id: int, addr: int, nbytes: int) -> bytes:
        dev = self._get_device_by_addr(bus_id, addr)
        return dev.read(nbytes)

    def writeto_mem(self, bus_id: int, addr: int, memaddr: int, data: bytes | bytearray):
        dev = self._get_device_by_addr(bus_id, addr)
        dev.write_mem(memaddr, data)

    def readfrom_mem(self, bus_id: int, addr: int, memaddr: int, nbytes: int) -> bytes:
        dev = self._get_device_by_addr(bus_id, addr)
        return dev.read_mem(memaddr, nbytes)

    def reset(self):
        self.buses.clear()
        
    def teardown(self):
        self.reset()
        self.net_resolver = None
        self.device_models.clear()
