from enum import Enum
from typing import Optional

class ServoSignalState(Enum):
    DISCONNECTED = 0
    NO_SIGNAL = 1
    INVALID_SIGNAL = 2
    VALID_SIGNAL = 3
    CONFLICT = 4

class ServoModel:
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.angle = 90.0
        self.target_angle = 90.0
        
        self.min_angle = 0.0
        self.max_angle = 180.0
        
        self.min_pulse_us = 500
        self.max_pulse_us = 2500
        
        self.current_pulse_us = 0.0
        self.frequency = 0.0
        
        self.signal_state = ServoSignalState.DISCONNECTED
        self.powered = False
        
        self.net_resolver = None

    def set_net_resolver(self, resolver):
        self.net_resolver = resolver
        self._check_power()

    def _check_power(self):
        if not self.net_resolver:
            self.powered = False
            return
            
        vcc_net = self.net_resolver.get_connected_pins(self.component_id, "vcc")
        gnd_net = self.net_resolver.get_connected_pins(self.component_id, "gnd")
        
        has_vcc = any(p_cid == "esp32" and (p_name.startswith("3V3") or p_name.startswith("5V") or p_name.startswith("VIN")) for p_cid, p_name in vcc_net)
        has_gnd = any(p_cid == "esp32" and p_name.startswith("GND") for p_cid, p_name in gnd_net)
        
        self.powered = has_vcc and has_gnd

    def set_pwm(self, freq: int, duty_norm: float):
        self._check_power()
        
        if not self.powered:
            self.signal_state = ServoSignalState.INVALID_SIGNAL
            return
            
        # If duty is exactly 0.0, it means no signal (e.g. topology disconnected it or turned off)
        if duty_norm <= 0.0:
            self.signal_state = ServoSignalState.NO_SIGNAL
            self.current_pulse_us = 0.0
            return
            
        if not (45 <= freq <= 55):
            self.signal_state = ServoSignalState.INVALID_SIGNAL
            return
            
        self.signal_state = ServoSignalState.VALID_SIGNAL
        self.frequency = freq
        
        # Calculate pulse width
        # Period in us = 1_000_000 / freq
        period_us = 1000000.0 / freq
        self.current_pulse_us = duty_norm * period_us
        
        # Validate pulse width
        if self.current_pulse_us < self.min_pulse_us or self.current_pulse_us > self.max_pulse_us:
            # We clamp the pulse for angle calculation, but if it's wildly out of bounds, maybe INVALID?
            # Let's clamp it.
            pass
            
        clamped_pulse = max(self.min_pulse_us, min(self.max_pulse_us, self.current_pulse_us))
        
        ratio = (clamped_pulse - self.min_pulse_us) / (self.max_pulse_us - self.min_pulse_us)
        self.target_angle = self.min_angle + ratio * (self.max_angle - self.min_angle)
        self.angle = self.target_angle
        
    def get_state_dict(self):
        return {
            'angle': self.angle,
            'signal_state': self.signal_state.name,
            'powered': self.powered
        }

    def to_dict(self):
        return {
            'angle': self.angle,
            'min_angle': self.min_angle,
            'max_angle': self.max_angle,
            'min_pulse_us': self.min_pulse_us,
            'max_pulse_us': self.max_pulse_us
        }
        
    def from_dict(self, data):
        self.angle = data.get('angle', 90.0)
        self.target_angle = self.angle
        self.min_angle = data.get('min_angle', 0.0)
        self.max_angle = data.get('max_angle', 180.0)
        self.min_pulse_us = data.get('min_pulse_us', 500)
        self.max_pulse_us = data.get('max_pulse_us', 2500)
