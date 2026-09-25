from typing import Optional
from ..core.models.board import create_default_esp32_wroom
from .gpio import GPIOManager

class ADCManager:
    """Gestionnaire de l'ADC (Analog to Digital Converter) pour la simulation."""
    
    def __init__(self, gpio_manager: GPIOManager):
        self.gpio_manager = gpio_manager
        self.board = create_default_esp32_wroom()
        self.net_resolver = None  # Injecté plus tard par le moteur ou l'UI
        self.device_models = {}   # id_composant -> objet modèle
        
    def configure(self, pin: int):
        pin_def = self.board.get_pin(pin)
        if not pin_def:
            raise ValueError(f"GPIO {pin} invalide.")
        if not pin_def.supports_adc:
            raise ValueError(f"Pin {pin} ne supporte pas l'ADC.")
            
    def read(self, pin: int) -> int:
        if not self.net_resolver:
            return 0  # Comportement par défaut si pas de topologie
            
        try:
            net = self.net_resolver.get_connected_pins("esp32", f"GPIO{pin}")
        except Exception:
            return 0
        if not net:
            return 0
            
        vcc = False
        gnd = False
        analog_values = []
        
        for comp_id, pin_id in net:
            pid_upper = pin_id.upper()
            if pid_upper in ("3V3", "VCC", "5V", "VIN"):
                vcc = True
            elif "GND" in pid_upper:
                gnd = True
            elif comp_id in self.device_models:
                dev = self.device_models[comp_id]
                if hasattr(dev, "get_analog_state"):
                    state = dev.get_analog_state(pin_id)
                    if state.status == "VALUE" and state.value is not None:
                        analog_values.append(state.value)
                        
        if vcc and gnd:
            return 0
        if vcc:
            return 4095
        if gnd:
            return 0
        if analog_values:
            return int(analog_values[0])
            
        return 0
        
    def read_u16(self, pin: int) -> int:
        return self.read(pin) * 16

    def reset(self):
        pass

    def teardown(self):
        self.device_models.clear()
        self.net_resolver = None
