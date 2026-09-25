class I2CDeviceModel:
    is_i2c_device = True
    sda_pin_name = "sda"
    scl_pin_name = "scl"
    
    def __init__(self, component_id: str, address: int):
        self.component_id = component_id
        self.address = address

    def write(self, data: bytes | bytearray):
        pass

    def read(self, nbytes: int) -> bytes:
        return bytes([0] * nbytes)

    def write_mem(self, memaddr: int, data: bytes | bytearray):
        pass

    def read_mem(self, memaddr: int, nbytes: int) -> bytes:
        return bytes([0] * nbytes)
        
class GenericI2CDevice(I2CDeviceModel):
    def __init__(self, component_id: str, address: int = 0x48):
        super().__init__(component_id, address)
        self.registers = {
            0x00: 0x12,
            0x01: 0x34,
            0x10: 0x00,
            0x11: 0x00
        }
        self.last_register = 0x00

    def write(self, data: bytes | bytearray):
        if not data:
            return
        self.last_register = data[0]
        if len(data) > 1:
            self.write_mem(self.last_register, data[1:])

    def read(self, nbytes: int) -> bytes:
        return self.read_mem(self.last_register, nbytes)

    def write_mem(self, memaddr: int, data: bytes | bytearray):
        for i, b in enumerate(data):
            # Only 0x10 and 0x11 are writable
            if (memaddr + i) in (0x10, 0x11):
                self.registers[memaddr + i] = b

    def read_mem(self, memaddr: int, nbytes: int) -> bytes:
        res = bytearray()
        for i in range(nbytes):
            res.append(self.registers.get(memaddr + i, 0x00))
        return bytes(res)
