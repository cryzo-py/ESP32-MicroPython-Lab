"""
Bibliothèque virtuelle 'Servo' pour Arduino C.
Permet de piloter un servomoteur connecté à une broche PWM (par exemple D9).
"""

from __future__ import annotations
from typing import Optional


class VirtualServo:
    """Implémentation virtuelle de la classe Servo Arduino."""

    def __init__(self, gpio_manager=None, pwm_manager=None):
        self.gpio_manager = gpio_manager
        self.pwm_manager = pwm_manager
        self.pin: Optional[int] = None
        self.angle: float = 90.0
        self.min_us: int = 544
        self.max_us: int = 2400

    def attach(self, pin: int | str, min_us: int = 544, max_us: int = 2400) -> int:
        """Attache le servomoteur à une broche numérique."""
        if isinstance(pin, str):
            p_clean = pin.upper().replace("GPIO", "").replace("D", "")
            pin_num = int(p_clean) if p_clean.isdigit() else 9
        else:
            pin_num = int(pin)

        self.pin = pin_num
        self.min_us = min_us
        self.max_us = max_us

        if self.pwm_manager:
            try:
                self.pwm_manager.configure(self.pin)
                self.pwm_manager.set_frequency(self.pin, 50)  # 50 Hz standard servomoteur
            except Exception:
                pass

        self.write(self.angle)
        return self.pin

    def write(self, angle: int | float):
        """Définit l'angle de consigne du servomoteur (0 à 180 degrés)."""
        clamped_angle = max(0.0, min(180.0, float(angle)))
        self.angle = clamped_angle

        if self.pin is None or not self.pwm_manager:
            return

        # Période pour 50 Hz = 20 000 µs
        pulse_us = self.min_us + (clamped_angle / 180.0) * (self.max_us - self.min_us)
        duty_norm = pulse_us / 20000.0

        # L'échelle interne PWM du simulateur (PWMManager) est 0-1023
        duty_val = int(duty_norm * 1023)
        try:
            self.pwm_manager.set_duty(self.pin, duty_val)
        except Exception:
            pass

    def writeMicroseconds(self, us: int):
        """Définit directement la largeur d'impulsion en microsecondes."""
        clamped_us = max(self.min_us, min(self.max_us, int(us)))
        angle = ((clamped_us - self.min_us) / float(self.max_us - self.min_us)) * 180.0
        self.write(angle)

    def read(self) -> int:
        """Retourne le dernier angle écrit."""
        return int(self.angle)

    def attached(self) -> bool:
        """Vérifie si le servo est actuellement attaché à une broche."""
        return self.pin is not None

    def detach(self):
        """Détache le servo et libère la ressource PWM."""
        if self.pin is not None and self.pwm_manager:
            try:
                self.pwm_manager.set_duty(self.pin, 0)
            except Exception:
                pass
        self.pin = None
