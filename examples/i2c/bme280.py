import time

class BME280:
    def __init__(self, i2c=None, address=0x76):
        self.i2c = i2c
        self.address = address
        
        # Check ID
        chip_id = self.i2c.readfrom_mem(self.address, 0xD0, 1)[0]
        if chip_id != 0x60:
            raise RuntimeError("Unknown chip ID: " + hex(chip_id))
            
        # Reset
        self.i2c.writeto_mem(self.address, 0xE0, b'\xB6')
        time.sleep(0.01)
        
        # Read calibration
        self._read_calibration()
        
        # Configure
        # ctrl_hum: osrs_h = 1 (1x oversampling)
        self.i2c.writeto_mem(self.address, 0xF2, b'\x01')
        
        # ctrl_meas: osrs_t=1 (1x), osrs_p=1 (1x), mode=3 (Normal)
        self.i2c.writeto_mem(self.address, 0xF4, b'\x27')
        
        # config: t_sb=0 (0.5ms), filter=0, spi3w_en=0
        self.i2c.writeto_mem(self.address, 0xF5, b'\x00')
        
    def _read_calibration(self):
        # T1-T3 (0x88 to 0x8D)
        b = self.i2c.readfrom_mem(self.address, 0x88, 6)
        self.dig_T1 = b[0] | (b[1] << 8)
        self.dig_T2 = b[2] | (b[3] << 8); if self.dig_T2 > 32767: self.dig_T2 -= 65536
        self.dig_T3 = b[4] | (b[5] << 8); if self.dig_T3 > 32767: self.dig_T3 -= 65536
        
        # P1-P9 (0x8E to 0x9F)
        b = self.i2c.readfrom_mem(self.address, 0x8E, 18)
        self.dig_P1 = b[0] | (b[1] << 8)
        self.dig_P2 = b[2] | (b[3] << 8); if self.dig_P2 > 32767: self.dig_P2 -= 65536
        self.dig_P3 = b[4] | (b[5] << 8); if self.dig_P3 > 32767: self.dig_P3 -= 65536
        self.dig_P4 = b[6] | (b[7] << 8); if self.dig_P4 > 32767: self.dig_P4 -= 65536
        self.dig_P5 = b[8] | (b[9] << 8); if self.dig_P5 > 32767: self.dig_P5 -= 65536
        self.dig_P6 = b[10] | (b[11] << 8); if self.dig_P6 > 32767: self.dig_P6 -= 65536
        self.dig_P7 = b[12] | (b[13] << 8); if self.dig_P7 > 32767: self.dig_P7 -= 65536
        self.dig_P8 = b[14] | (b[15] << 8); if self.dig_P8 > 32767: self.dig_P8 -= 65536
        self.dig_P9 = b[16] | (b[17] << 8); if self.dig_P9 > 32767: self.dig_P9 -= 65536
        
        # H1-H6
        self.dig_H1 = self.i2c.readfrom_mem(self.address, 0xA1, 1)[0]
        b = self.i2c.readfrom_mem(self.address, 0xE1, 7)
        self.dig_H2 = b[0] | (b[1] << 8); if self.dig_H2 > 32767: self.dig_H2 -= 65536
        self.dig_H3 = b[2]
        self.dig_H4 = (b[3] << 4) | (b[4] & 0x0F); if self.dig_H4 > 2047: self.dig_H4 -= 4096
        self.dig_H5 = (b[5] << 4) | (b[4] >> 4); if self.dig_H5 > 2047: self.dig_H5 -= 4096
        self.dig_H6 = b[6]; if self.dig_H6 > 127: self.dig_H6 -= 256
        
    def read_compensated_data(self):
        b = self.i2c.readfrom_mem(self.address, 0xF7, 8)
        
        adc_p = (b[0] << 12) | (b[1] << 4) | (b[2] >> 4)
        adc_t = (b[3] << 12) | (b[4] << 4) | (b[5] >> 4)
        adc_h = (b[6] << 8) | b[7]
        
        var1 = ((((adc_t >> 3) - (self.dig_T1 << 1))) * (self.dig_T2)) >> 11
        var2 = (((((adc_t >> 4) - (self.dig_T1)) * ((adc_t >> 4) - (self.dig_T1))) >> 12) * (self.dig_T3)) >> 14
        t_fine = var1 + var2
        T = (t_fine * 5 + 128) >> 8
        
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1)) * self.dig_P1 >> 33
        if var1 == 0:
            P = 0
        else:
            p = 1048576 - adc_p
            p = int((((p << 31) - var2) * 3125) / var1)
            var1 = ((self.dig_P9) * (p >> 13) * (p >> 13)) >> 25
            var2 = ((self.dig_P8) * p) >> 19
            P = ((p + var1 + var2) >> 8) + ((self.dig_P7) << 4)
            
        v_x1_u32r = t_fine - 76800
        v_x1_u32r = ((((adc_h << 14) - (self.dig_H4 << 20) - (self.dig_H5 * v_x1_u32r)) + 16384) >> 15) * \
                    (((((((v_x1_u32r * self.dig_H6) >> 10) * (((v_x1_u32r * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) * self.dig_H2 + 8192) >> 14)
        v_x1_u32r = v_x1_u32r - (((((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7) * self.dig_H1) >> 4)
        if v_x1_u32r < 0: v_x1_u32r = 0
        if v_x1_u32r > 419430400: v_x1_u32r = 419430400
        H = v_x1_u32r >> 12
        
        return T, P, H
        
    @property
    def temperature(self):
        t, p, h = self.read_compensated_data()
        return str(t / 100.0) + "C"
        
    @property
    def pressure(self):
        t, p, h = self.read_compensated_data()
        return str(p / 256.0) + "hPa"
        
    @property
    def humidity(self):
        t, p, h = self.read_compensated_data()
        return str(h / 1024.0) + "%"
