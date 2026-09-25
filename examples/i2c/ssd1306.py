import time

# I2C driver for SSD1306 displays

class SSD1306_I2C:
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        
        self.init_display()

    def init_display(self):
        for cmd in (
            0xAE,       # display off
            0x20, 0x00, # addressing mode (0x00 = Horizontal)
            0x40,       # display start line 0
            0xA1,       # segment remap 1
            0xA8, self.height - 1, # multiplex ratio
            0xC8,       # COM output scan direction
            0xD3, 0x00, # display offset
            0xDA, 0x02 if self.height == 32 else 0x12, # COM pins hardware conf
            0xD5, 0x80, # display clock divide
            0xD9, 0x22 if self.external_vcc else 0xF1, # pre-charge period
            0xDB, 0x30, # VCOMH deselect level
            0x81, 0xFF, # contrast
            0xA4,       # output follows RAM content
            0xA6,       # normal display (not inverted)
            0x8D, 0x10 if self.external_vcc else 0x14, # charge pump
            0xAF,       # display on
        ):
            self.write_cmd(cmd)
        
        self.fill(0)
        self.show()

    def write_cmd(self, cmd):
        self.i2c.writeto_mem(self.addr, 0x00, bytes([cmd]))

    def write_data(self, buf):
        self.i2c.writeto_mem(self.addr, 0x40, buf)

    def poweroff(self):
        self.write_cmd(0xAE)

    def poweron(self):
        self.write_cmd(0xAF)

    def contrast(self, contrast):
        self.write_cmd(0x81)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(0xA6 | (invert & 1))

    def show(self):
        # Setting col and page address window
        self.write_cmd(0x21)
        self.write_cmd(0)
        self.write_cmd(self.width - 1)
        self.write_cmd(0x22)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        
        self.write_data(self.buffer)

    def fill(self, col):
        fill_byte = 0xFF if col else 0x00
        for i in range(len(self.buffer)):
            self.buffer[i] = fill_byte

    def pixel(self, x, y, col):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        page = y // 8
        bit = y % 8
        idx = page * self.width + x
        if col:
            self.buffer[idx] |= (1 << bit)
        else:
            self.buffer[idx] &= ~(1 << bit)

    def text(self, string, x, y, col=1):
        # A very basic 8x8 font rendering function for the simulator
        font_8x8 = {
            ' ': [0x00]*8,
            'A': [0x7E, 0x11, 0x11, 0x11, 0x7E, 0x00, 0x00, 0x00],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36, 0x00, 0x00, 0x00],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22, 0x00, 0x00, 0x00],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41, 0x00, 0x00, 0x00],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F, 0x00, 0x00, 0x00],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40, 0x00, 0x00, 0x00],
            'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F, 0x00, 0x00, 0x00],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E, 0x00, 0x00, 0x00],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06, 0x00, 0x00, 0x00],
            'S': [0x26, 0x49, 0x49, 0x49, 0x32, 0x00, 0x00, 0x00],
            'T': [0x01, 0x01, 0x7F, 0x01, 0x01, 0x00, 0x00, 0x00],
            'c': [0x38, 0x44, 0x44, 0x44, 0x20, 0x00, 0x00, 0x00],
            'e': [0x38, 0x54, 0x54, 0x54, 0x18, 0x00, 0x00, 0x00],
            'i': [0x00, 0x44, 0x7D, 0x40, 0x00, 0x00, 0x00, 0x00],
            'l': [0x00, 0x41, 0x7F, 0x40, 0x00, 0x00, 0x00, 0x00],
            'o': [0x38, 0x44, 0x44, 0x44, 0x38, 0x00, 0x00, 0x00],
            'p': [0x7C, 0x14, 0x14, 0x14, 0x08, 0x00, 0x00, 0x00],
            'r': [0x7C, 0x08, 0x04, 0x04, 0x08, 0x00, 0x00, 0x00],
            'y': [0x4C, 0x50, 0x50, 0x50, 0x3C, 0x00, 0x00, 0x00],
            '2': [0x62, 0x51, 0x49, 0x49, 0x46, 0x00, 0x00, 0x00],
            '3': [0x22, 0x41, 0x49, 0x49, 0x36, 0x00, 0x00, 0x00],
        }
        
        curr_x = x
        for char in string:
            glyph = font_8x8.get(char)
            if not glyph:
                # Fallback simple block
                glyph = [0xFF]*5 + [0x00]*3
                
            for col_idx, col_val in enumerate(glyph):
                if curr_x + col_idx >= self.width:
                    break
                for row_idx in range(8):
                    if (col_val >> row_idx) & 1:
                        self.pixel(curr_x + col_idx, y + row_idx, col)
            curr_x += 8
