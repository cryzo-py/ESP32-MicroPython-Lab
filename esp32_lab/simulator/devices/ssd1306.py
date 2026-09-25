from esp32_lab.simulator.devices.i2c_device import I2CDeviceModel
from esp32_lab.app.event_bus import get_event_bus

class SSD1306Model(I2CDeviceModel):
    def __init__(self, component_id: str, address: int = 0x3C, width: int = 128, height: int = 64):
        super().__init__(component_id, address)
        self.width = width
        self.height = height
        
        self.pages = height // 8
        self.framebuffer = bytearray(self.pages * width)
        
        self.is_on = False
        self.inverted = False
        self.contrast = 0x7F
        
        # Addressing
        # 0 = Horizontal, 1 = Vertical, 2 = Page
        self.addressing_mode = 2 
        
        self.col_start = 0
        self.col_end = width - 1
        self.page_start = 0
        self.page_end = self.pages - 1
        
        self.curr_col = 0
        self.curr_page = 0
        
        self.event_bus = get_event_bus()

    def reset(self):
        self.is_on = False
        self.inverted = False
        self.contrast = 0x7F
        self.addressing_mode = 2
        self.col_start = 0
        self.col_end = self.width - 1
        self.page_start = 0
        self.page_end = self.pages - 1
        self.curr_col = 0
        self.curr_page = 0
        self.framebuffer = bytearray(self.pages * self.width)
        self._notify_update()

    def write(self, data: bytes | bytearray):
        if not data:
            return
            
        control = data[0]
        payload = data[1:]
        
        if control == 0x00:  # Command stream
            self._handle_commands(payload)
        elif control == 0x40:  # Data stream
            self._handle_data(payload)
        elif control == 0x80:  # Single command
            self._handle_commands(payload)

    def read(self, nbytes: int) -> bytes:
        # SSD1306 typically does not support reading display RAM over I2C
        return bytes([0x00] * nbytes)

    def write_mem(self, memaddr: int, data: bytes | bytearray):
        # We can simulate MicroPython's writeto_mem(0x3C, 0x00, cmds)
        if memaddr == 0x00:
            self._handle_commands(data)
        elif memaddr == 0x40:
            self._handle_data(data)

    def read_mem(self, memaddr: int, nbytes: int) -> bytes:
        return bytes([0x00] * nbytes)

    def _handle_commands(self, cmds: bytes):
        if not hasattr(self, '_cmd_buffer'):
            self._cmd_buffer = []
        self._cmd_buffer.extend(cmds)
        
        i = 0
        while i < len(self._cmd_buffer):
            cmd = self._cmd_buffer[i]
            if cmd == 0xAE: # Display OFF
                self.is_on = False
                i += 1
            elif cmd == 0xAF: # Display ON
                self.is_on = True
                i += 1
            elif cmd == 0x20: # Addressing mode
                if i + 1 < len(self._cmd_buffer):
                    self.addressing_mode = self._cmd_buffer[i+1] & 0x03
                    i += 2
                else:
                    break
            elif cmd == 0x21: # Column address
                if i + 2 < len(self._cmd_buffer):
                    self.col_start = self._cmd_buffer[i+1]
                    self.col_end = self._cmd_buffer[i+2]
                    self.curr_col = self.col_start
                    i += 3
                else:
                    break
            elif cmd == 0x22: # Page address
                if i + 2 < len(self._cmd_buffer):
                    self.page_start = self._cmd_buffer[i+1]
                    self.page_end = self._cmd_buffer[i+2]
                    self.curr_page = self.page_start
                    i += 3
                else:
                    break
            elif 0xB0 <= cmd <= 0xB7: # Set Page Start Address for Page Addressing Mode
                self.curr_page = cmd & 0x0F
                i += 1
            elif cmd == 0x81: # Contrast
                if i + 1 < len(self._cmd_buffer):
                    self.contrast = self._cmd_buffer[i+1]
                    i += 2
                else:
                    break
            elif cmd == 0xA6: # Normal display
                self.inverted = False
                i += 1
            elif cmd == 0xA7: # Inverted display
                self.inverted = True
                i += 1
            elif 0x00 <= cmd <= 0x0F: # set lower column start
                self.curr_col = (self.curr_col & 0xF0) | (cmd & 0x0F)
                i += 1
            elif 0x10 <= cmd <= 0x1F: # set higher column start
                self.curr_col = ((cmd & 0x0F) << 4) | (self.curr_col & 0x0F)
                i += 1
            elif cmd in [0xA4, 0xA5, 0xC0, 0xC8, 0xE3, 0x8D, 0xA0, 0xA1]: # 1-byte ignored commands
                i += 1
            elif cmd in [0xD3, 0xD5, 0xD9, 0xDA, 0xDB]: # 2-byte ignored commands
                if i + 1 < len(self._cmd_buffer):
                    i += 2
                else:
                    break
            elif cmd == 0xA8: # 2-byte multiplex ratio
                if i + 1 < len(self._cmd_buffer):
                    i += 2
                else:
                    break
            else:
                # unknown command, skip 1 byte
                i += 1
        
        # Remove processed commands
        self._cmd_buffer = self._cmd_buffer[i:]
        self._notify_update()

    def _handle_data(self, data: bytes):
        updated = False
        for byte in data:
            if 0 <= self.curr_col < self.width and 0 <= self.curr_page < self.pages:
                idx = self.curr_page * self.width + self.curr_col
                if idx < len(self.framebuffer):
                    self.framebuffer[idx] = byte
                    updated = True
                
            # Advance address
            if self.addressing_mode == 0: # Horizontal
                self.curr_col += 1
                if self.curr_col > self.col_end:
                    self.curr_col = self.col_start
                    self.curr_page += 1
                    if self.curr_page > self.page_end:
                        self.curr_page = self.page_start
            elif self.addressing_mode == 1: # Vertical
                self.curr_page += 1
                if self.curr_page > self.page_end:
                    self.curr_page = self.page_start
                    self.curr_col += 1
                    if self.curr_col > self.col_end:
                        self.curr_col = self.col_start
            elif self.addressing_mode == 2: # Page
                self.curr_col += 1
                if self.curr_col >= self.width:
                    self.curr_col = 0
                    
        if updated:
            self._notify_update()

    def _notify_update(self):
        # We notify the UI of the framebuffer
        # The visual layer will handle is_on and inverted
        buf = bytearray(self.framebuffer)
        if not self.is_on:
            buf = bytearray(len(buf)) # Black if off
        elif self.inverted:
            buf = bytearray(~b & 0xFF for b in buf) # Inverted
            
        self.event_bus.display_updated.emit(self.component_id, self.width, self.height, bytes(buf))
