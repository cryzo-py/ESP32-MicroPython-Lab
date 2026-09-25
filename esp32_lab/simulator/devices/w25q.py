import math
from .spi_device import SPIDeviceModel

class W25QxxModel(SPIDeviceModel):
    def __init__(self, component_id: str, variant: str = "W25Q32"):
        super().__init__(component_id)
        self.variant = variant
        
        if variant == "W25Q64":
            self.capacity = 8 * 1024 * 1024 # 8 MiB
            self.jedec_id = b'\xEF\x40\x17'
        else: # Default W25Q32
            self.capacity = 4 * 1024 * 1024 # 4 MiB
            self.jedec_id = b'\xEF\x40\x16'
            
        self.page_size = 256
        self.sector_size = 4096
        
        # We use a bytearray for memory to simulate flash (default 0xFF)
        # 4-8MB is small enough to hold in RAM, but we could use a dict for sparse storage.
        # Let's use a dictionary of 4KB sectors for sparsity to save memory and init time.
        self.memory = {}
        
        # Status registers
        self.wel = False # Write Enable Latch
        self.busy = False # Busy state
        
    def reset_runtime(self):
        """Reset operational state (not memory)"""
        self.wel = False
        self.busy = False
        
    def reset_memory(self):
        """Chip erase"""
        self.memory.clear()
        
    def _get_sector(self, sector_index: int) -> bytearray:
        if sector_index not in self.memory:
            self.memory[sector_index] = bytearray([0xFF] * self.sector_size)
        return self.memory[sector_index]
        
    def _read_byte(self, address: int) -> int:
        if address < 0 or address >= self.capacity:
            return 0xFF
        sector_index = address // self.sector_size
        if sector_index not in self.memory:
            return 0xFF
        return self.memory[sector_index][address % self.sector_size]
        
    def _write_byte(self, address: int, value: int):
        if address < 0 or address >= self.capacity:
            return
        sector_index = address // self.sector_size
        sector = self._get_sector(sector_index)
        offset = address % self.sector_size
        # NOR flash can only clear bits (1 -> 0)
        sector[offset] &= value

    def spi_transfer(self, tx_data: bytes, polarity: int, phase: int) -> bytes:
        if not tx_data:
            return b""
            
        cmd = tx_data[0]
        rx_data = bytearray([0xFF] * len(tx_data))
        
        if cmd == 0x9F: # JEDEC ID
            for i in range(min(3, len(tx_data) - 1)):
                rx_data[i+1] = self.jedec_id[i]
                
        elif cmd == 0x05: # Read Status Register 1
            status = 0
            if self.busy: status |= 0x01
            if self.wel: status |= 0x02
            for i in range(1, len(tx_data)):
                rx_data[i] = status
                
        elif cmd == 0x06: # Write Enable
            self.wel = True
            
        elif cmd == 0x04: # Write Disable
            self.wel = False
            
        elif cmd == 0x03 or cmd == 0x0B: # Read Data or Fast Read
            dummy_cycles = 1 if cmd == 0x0B else 0
            if len(tx_data) > 4 + dummy_cycles:
                addr = (tx_data[1] << 16) | (tx_data[2] << 8) | tx_data[3]
                data_start = 4 + dummy_cycles
                for i in range(data_start, len(tx_data)):
                    rx_data[i] = self._read_byte(addr)
                    addr += 1
                    
        elif cmd == 0x02: # Page Program
            if self.wel and not self.busy and len(tx_data) > 4:
                addr = (tx_data[1] << 16) | (tx_data[2] << 8) | tx_data[3]
                page_start = addr & ~(self.page_size - 1)
                for i in range(4, len(tx_data)):
                    # Wrap around page boundary
                    write_addr = page_start | (addr & (self.page_size - 1))
                    self._write_byte(write_addr, tx_data[i])
                    addr += 1
                self.wel = False
                
        elif cmd == 0x20: # Sector Erase (4KB)
            if self.wel and not self.busy and len(tx_data) >= 4:
                addr = (tx_data[1] << 16) | (tx_data[2] << 8) | tx_data[3]
                sector_index = addr // self.sector_size
                if sector_index in self.memory:
                    del self.memory[sector_index]
                self.wel = False
                
        elif cmd == 0xC7 or cmd == 0x60: # Chip Erase
            if self.wel and not self.busy:
                self.reset_memory()
                self.wel = False
                
        elif cmd == 0x66: # Enable Reset
            pass # We could set a flag waiting for 0x99
            
        elif cmd == 0x99: # Reset
            self.reset_runtime()

        return bytes(rx_data)

    def to_dict(self) -> dict:
        # Save memory only if we have configured persistence policy for it
        # Actually, for 4-8MB sparse, we could save the modified sectors as hex strings
        mem_data = {}
        for s_idx, s_data in self.memory.items():
            mem_data[s_idx] = s_data.hex()
            
        return {
            "variant": self.variant,
            "memory": mem_data
        }
        
    def from_dict(self, data: dict):
        if "variant" in data:
            self.variant = data["variant"]
        if "memory" in data:
            self.memory.clear()
            for s_idx_str, s_hex in data["memory"].items():
                self.memory[int(s_idx_str)] = bytearray.fromhex(s_hex)
