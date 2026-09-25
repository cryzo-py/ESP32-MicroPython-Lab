"""
Module MicroPython de simulation pour centrale inertielle MPU-6050 / GY-521 (I2C).
Fournit accéléromètre 3 axes (X, Y, Z), gyroscope 3 axes et température interne.
"""


class MPU6050:
    """Pilote MicroPython émulé pour centrale inertielle 6 axes MPU6050."""

    def __init__(self, i2c=None, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self._accel = {"x": 0.02, "y": -0.01, "z": 0.99} # Accélérations en g
        self._gyro = {"x": 0.1, "y": 0.0, "z": -0.2}     # Vitesse angulaire en °/s
        self._temp = 25.4                                  # Température puce °C

    def get_accel(self) -> dict:
        """Retourne un dictionnaire {'x': ax, 'y': ay, 'z': az} en g."""
        return dict(self._accel)

    def get_gyro(self) -> dict:
        """Retourne un dictionnaire {'x': gx, 'y': gy, 'z': gz} en °/s."""
        return dict(self._gyro)

    def get_temp(self) -> float:
        """Retourne la température interne du capteur en °C."""
        return self._temp

    def get_values(self) -> dict:
        """Dictionnaire complet standard MicroPython."""
        return {
            "AcX": int(self._accel["x"] * 16384),
            "AcY": int(self._accel["y"] * 16384),
            "AcZ": int(self._accel["z"] * 16384),
            "GyX": int(self._gyro["x"] * 131),
            "GyY": int(self._gyro["y"] * 131),
            "GyZ": int(self._gyro["z"] * 131),
            "Tmp": self._temp,
        }

    @property
    def accel(self):
        class AccelObj:
            x = 0.02
            y = -0.01
            z = 0.99
        return AccelObj()

    @property
    def gyro(self):
        class GyroObj:
            x = 0.1
            y = 0.0
            z = -0.2
        return GyroObj()
