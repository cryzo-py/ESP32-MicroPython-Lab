from esp32_lab.simulator.devices.i2c_device import I2CDeviceModel

class BME280Model(I2CDeviceModel):
    def __init__(self, component_id: str, address: int = 0x76,
                 temperature: float = 24.5, humidity: float = 52.0, pressure: float = 1013.25):
        super().__init__(component_id, address)
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        
        # BME280 standard registers
        self.registers = {
            0xD0: 0x60, # Chip ID
            0xF2: 0x00, # ctrl_hum
            0xF3: 0x00, # status
            0xF4: 0x00, # ctrl_meas
            0xF5: 0x00, # config
        }
        
        # Calibration registers
        # Using real typical values for accurate simulation
        self.calib = {
            'dig_T1': 27504, 'dig_T2': 26435, 'dig_T3': -1000,
            'dig_P1': 36477, 'dig_P2': -10685, 'dig_P3': 3024,
            'dig_P4': 2855, 'dig_P5': 140, 'dig_P6': -7,
            'dig_P7': 15500, 'dig_P8': -14600, 'dig_P9': 6000,
            'dig_H1': 75, 'dig_H2': 360, 'dig_H3': 0,
            'dig_H4': 300, 'dig_H5': 0, 'dig_H6': 30
        }
        self._populate_calib_registers()
        
        self.last_register = 0x00
        
    def _populate_calib_registers(self):
        # T1 to T3
        self.registers[0x88] = self.calib['dig_T1'] & 0xFF
        self.registers[0x89] = (self.calib['dig_T1'] >> 8) & 0xFF
        self.registers[0x8A] = self.calib['dig_T2'] & 0xFF
        self.registers[0x8B] = (self.calib['dig_T2'] >> 8) & 0xFF
        self.registers[0x8C] = self.calib['dig_T3'] & 0xFF
        self.registers[0x8D] = (self.calib['dig_T3'] >> 8) & 0xFF
        
        # P1 to P9
        addr = 0x8E
        for p in range(1, 10):
            val = self.calib[f'dig_P{p}']
            self.registers[addr] = val & 0xFF
            self.registers[addr+1] = (val >> 8) & 0xFF
            addr += 2
            
        # H1
        self.registers[0xA1] = self.calib['dig_H1']
        
        # H2 to H6 (0xE1 to 0xE7)
        self.registers[0xE1] = self.calib['dig_H2'] & 0xFF
        self.registers[0xE2] = (self.calib['dig_H2'] >> 8) & 0xFF
        self.registers[0xE3] = self.calib['dig_H3']
        self.registers[0xE4] = (self.calib['dig_H4'] >> 4) & 0xFF
        self.registers[0xE5] = (self.calib['dig_H4'] & 0x0F) | ((self.calib['dig_H5'] & 0x0F) << 4)
        self.registers[0xE6] = (self.calib['dig_H5'] >> 4) & 0xFF
        self.registers[0xE7] = self.calib['dig_H6'] & 0xFF
        
    def _compensate_T(self, adc_T):
        var1 = ((((adc_T >> 3) - (self.calib['dig_T1'] << 1))) * (self.calib['dig_T2'])) >> 11
        var2 = (((((adc_T >> 4) - (self.calib['dig_T1'])) * ((adc_T >> 4) - (self.calib['dig_T1']))) >> 12) * (self.calib['dig_T3'])) >> 14
        t_fine = var1 + var2
        T = (t_fine * 5 + 128) >> 8
        return T, t_fine

    def _compensate_P(self, adc_P, t_fine):
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.calib['dig_P6']
        var2 = var2 + ((var1 * self.calib['dig_P5']) << 17)
        var2 = var2 + (self.calib['dig_P4'] << 35)
        var1 = ((var1 * var1 * self.calib['dig_P3']) >> 8) + ((var1 * self.calib['dig_P2']) << 12)
        var1 = (((1 << 47) + var1)) * self.calib['dig_P1'] >> 33
        if var1 == 0: return 0
        p = 1048576 - adc_P
        p = int((((p << 31) - var2) * 3125) / var1)
        var1 = ((self.calib['dig_P9']) * (p >> 13) * (p >> 13)) >> 25
        var2 = ((self.calib['dig_P8']) * p) >> 19
        p = ((p + var1 + var2) >> 8) + ((self.calib['dig_P7']) << 4)
        return p

    def _compensate_H(self, adc_H, t_fine):
        v_x1_u32r = t_fine - 76800
        v_x1_u32r = ((((adc_H << 14) - (self.calib['dig_H4'] << 20) - (self.calib['dig_H5'] * v_x1_u32r)) + 16384) >> 15) * \
                    (((((((v_x1_u32r * self.calib['dig_H6']) >> 10) * (((v_x1_u32r * self.calib['dig_H3']) >> 11) + 32768)) >> 10) + 2097152) * self.calib['dig_H2'] + 8192) >> 14)
        v_x1_u32r = v_x1_u32r - (((((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7) * self.calib['dig_H1']) >> 4)
        if v_x1_u32r < 0: v_x1_u32r = 0
        if v_x1_u32r > 419430400: v_x1_u32r = 419430400
        return v_x1_u32r >> 12

    def _find_adc_values(self):
        target_T = int(self.temperature * 100)
        
        # Binary search for T
        low, high = 0, 1048575
        adc_T = 524288
        t_fine = 0
        for _ in range(25):
            mid = (low + high) // 2
            T, t_f = self._compensate_T(mid)
            if T < target_T: low = mid
            else: high = mid
            adc_T = mid
            t_fine = t_f
            
        target_P = int(self.pressure * 256)
        low, high = 0, 1048575
        adc_P = 524288
        for _ in range(25):
            mid = (low + high) // 2
            P = self._compensate_P(mid, t_fine)
            if P > target_P: low = mid
            else: high = mid
            adc_P = mid
            
        target_H = int(self.humidity * 1024)
        low, high = 0, 65535
        adc_H = 32768
        for _ in range(20):
            mid = (low + high) // 2
            H = self._compensate_H(mid, t_fine)
            if H < target_H: low = mid
            else: high = mid
            adc_H = mid
            
        return adc_T, adc_P, adc_H
        
    def write(self, data: bytes | bytearray):
        if not data: return
        self.last_register = data[0]
        if len(data) > 1:
            self.write_mem(self.last_register, data[1:])
            
    def read(self, nbytes: int) -> bytes:
        return self.read_mem(self.last_register, nbytes)
        
    def write_mem(self, memaddr: int, data: bytes | bytearray):
        for i, b in enumerate(data):
            reg = memaddr + i
            if reg == 0xE0 and b == 0xB6:
                # Reset
                self.registers[0xF2] = 0x00
                self.registers[0xF3] = 0x00
                self.registers[0xF4] = 0x00
                self.registers[0xF5] = 0x00
            elif reg in (0xF2, 0xF4, 0xF5):
                self.registers[reg] = b
                
    def read_mem(self, memaddr: int, nbytes: int) -> bytes:
        # Update raw data if reading any measurement register (0xF7 to 0xFE)
        # BME280 usually updates all registers atomically during a burst read, 
        # so updating whenever we hit this range is safe for simulation.
        if (memaddr <= 0xFE) and (memaddr + nbytes > 0xF7):
            adc_T, adc_P, adc_H = self._find_adc_values()
            self.registers[0xF7] = (adc_P >> 12) & 0xFF
            self.registers[0xF8] = (adc_P >> 4) & 0xFF
            self.registers[0xF9] = (adc_P & 0x0F) << 4
            self.registers[0xFA] = (adc_T >> 12) & 0xFF
            self.registers[0xFB] = (adc_T >> 4) & 0xFF
            self.registers[0xFC] = (adc_T & 0x0F) << 4
            self.registers[0xFD] = (adc_H >> 8) & 0xFF
            self.registers[0xFE] = adc_H & 0xFF
            
        res = bytearray()
        for i in range(nbytes):
            res.append(self.registers.get(memaddr + i, 0x00))
        return bytes(res)
