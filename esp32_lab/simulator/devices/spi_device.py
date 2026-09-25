from abc import ABC, abstractmethod

class SPIDeviceModel(ABC):
    def __init__(self, component_id: str):
        self.component_id = component_id
        # Physical pin names on the component
        self.spi_sck_pin = "sck"
        self.spi_mosi_pin = "mosi"
        self.spi_miso_pin = "miso"
        self.spi_cs_pin = "cs"
        
    @abstractmethod
    def spi_transfer(self, tx_data: bytes, polarity: int, phase: int) -> bytes:
        """
        Processes an SPI transaction.
        tx_data: bytes sent by the master.
        Returns: bytes to be received by the master.
        """
        pass

class GenericSPIDevice(SPIDeviceModel):
    """
    A generic SPI device for testing. 
    Responds to 0x9F (JEDEC ID) with EF 40 18.
    Responds to 0x00 with 0x42.
    """
    def spi_transfer(self, tx_data: bytes, polarity: int, phase: int) -> bytes:
        if not tx_data:
            return b""
            
        cmd = tx_data[0]
        rx = bytearray(len(tx_data))
        
        if cmd == 0x9F:
            if len(rx) > 1:
                rx[1] = 0xEF
            if len(rx) > 2:
                rx[2] = 0x40
            if len(rx) > 3:
                rx[3] = 0x18
        elif cmd == 0x00:
            if len(rx) > 1:
                rx[1] = 0x42
                
        return bytes(rx)
