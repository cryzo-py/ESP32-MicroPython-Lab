import time

# I2C driver for SSD1306 displays

# Display listener registry (used by components/oled.py)
_display_listeners = []

def add_display_listener(callback):
    """Register a callback to be notified on display updates."""
    if callback not in _display_listeners:
        _display_listeners.append(callback)

def remove_display_listener(callback):
    """Unregister a display update callback."""
    if callback in _display_listeners:
        _display_listeners.remove(callback)

def _notify_display_listeners(width, height, buffer):
    """Notify all listeners of a display buffer update."""
    for cb in _display_listeners:
        try:
            cb(width, height, buffer)
        except Exception:
            pass

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
        try:
            from .font import font_data
        except ImportError:
            font_data = None
        
        curr_x = x
        for char in string:
            c = ord(char)
            if font_data and 32 <= c <= 126:
                offset = (c - 32) * 8
                glyph = font_data[offset:offset+8]
            else:
                glyph = [0xFF]*5 + [0x00]*3
                
            for col_idx, col_val in enumerate(glyph):
                if curr_x + col_idx >= self.width:
                    break
                for row_idx in range(8):
                    if (col_val >> row_idx) & 1:
                        self.pixel(curr_x + col_idx, y + row_idx, col)
            curr_x += 8

    def hline(self, x, y, w, col):
        for i in range(x, x + w):
            self.pixel(i, y, col)

    def vline(self, x, y, h, col):
        for i in range(y, y + h):
            self.pixel(x, i, col)

    def rect(self, x, y, w, h, col):
        self.hline(x, y, w, col)
        self.hline(x, y + h - 1, w, col)
        self.vline(x, y, h, col)
        self.vline(x + w - 1, y, h, col)

    def fill_rect(self, x, y, w, h, col):
        for i in range(y, y + h):
            self.hline(x, i, w, col)

    def line(self, x0, y0, x1, y1, col):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.pixel(x0, y0, col)
            if x0 == x1 and y0 == y1:
                break
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
