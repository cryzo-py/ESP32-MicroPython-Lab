class W25Qxx:
    def __init__(self, spi, cs_pin):
        self.spi = spi
        self.cs = cs_pin
        self.cs.value(1)
        
    def _transfer(self, tx_data, rx_len=0):
        self.cs.value(0)
        tx_buf = bytearray(tx_data)
        if rx_len > 0:
            rx_buf = bytearray(rx_len)
            self.spi.write_readinto(tx_buf, rx_buf)
            res = rx_buf
        else:
            self.spi.write(tx_buf)
            res = None
        self.cs.value(1)
        return res
        
    def read_jedec_id(self):
        tx = bytearray([0x9F, 0x00, 0x00, 0x00])
        rx = self._transfer(tx, 4)
        return bytes(rx[1:])
        
    def read_status(self):
        tx = bytearray([0x05, 0x00])
        rx = self._transfer(tx, 2)
        return rx[1]
        
    def write_enable(self):
        self._transfer([0x06])
        
    def write_disable(self):
        self._transfer([0x04])
        
    def read(self, address, length):
        tx = bytearray([0x03, (address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF])
        tx.extend(b'\x00' * length)
        rx = self._transfer(tx, len(tx))
        return bytes(rx[4:])
        
    def fast_read(self, address, length):
        tx = bytearray([0x0B, (address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF, 0x00])
        tx.extend(b'\x00' * length)
        rx = self._transfer(tx, len(tx))
        return bytes(rx[5:])
        
    def page_program(self, address, data):
        self.write_enable()
        tx = bytearray([0x02, (address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF])
        tx.extend(data)
        self._transfer(tx)
        
    def sector_erase(self, address):
        self.write_enable()
        tx = bytearray([0x20, (address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF])
        self._transfer(tx)
        
    def chip_erase(self):
        self.write_enable()
        self._transfer([0xC7])
        
    def wait_ready(self):
        while self.read_status() & 0x01:
            pass
