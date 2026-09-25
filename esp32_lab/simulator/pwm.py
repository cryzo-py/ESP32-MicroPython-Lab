from ..core.models.board import create_default_esp32_wroom
from .gpio import GPIOManager

class PWMManager:
    def __init__(self, gpio_manager: GPIOManager):
        self.gpio_manager = gpio_manager
        self.board = create_default_esp32_wroom()
        self.net_resolver = None
        self.device_models = {}
        
        # pin -> {'freq': int, 'duty': int, 'enabled': bool}
        self._states = {}
        
    def configure(self, pin: int):
        pin_def = self.board.get_pin(pin)
        if not pin_def:
            raise ValueError(f"GPIO {pin} invalide.")
        if not pin_def.supports_output:
            raise ValueError(f"Pin {pin} est Input-Only.")
        if not getattr(pin_def, 'pwm_supported', True):
            raise ValueError(f"Pin {pin} ne supporte pas le PWM.")
            
        if pin not in self._states:
            self._states[pin] = {'freq': 1000, 'duty': 0, 'enabled': True}
            
    def get(self, pin: int):
        return self._states.get(pin)

    def set_frequency(self, pin: int, freq: int):
        if freq <= 0:
            raise ValueError("La frequence doit etre positive.")
        self.configure(pin)
        self._states[pin]['freq'] = freq
        self._update_devices(pin)

    def get_frequency(self, pin: int) -> int:
        state = self._states.get(pin)
        return state['freq'] if state else 1000

    def set_duty(self, pin: int, duty: int):
        # MicroPython API: 0-1023
        if not (0 <= duty <= 1023):
            raise ValueError("Le rapport cyclique doit etre entre 0 et 1023.")
        self.configure(pin)
        self._states[pin]['duty'] = duty
        self._update_devices(pin)

    def get_duty(self, pin: int) -> int:
        state = self._states.get(pin)
        return state['duty'] if state else 0

    def deinit(self, pin: int):
        if pin in self._states:
            self._states[pin]['enabled'] = False
            self._states[pin]['duty'] = 0
            self._update_devices(pin)
            del self._states[pin]
            
    def reset(self):
        # Reset all pins to 0 and disable
        for pin in list(self._states.keys()):
            self.deinit(pin)
        self._states.clear()

    def teardown(self):
        self.reset()
        self.device_models.clear()
        self.net_resolver = None

    def _update_devices(self, pin: int):
        # Propagate through topology
        if not self.net_resolver:
            return
            
        state = self._states.get(pin)
        if not state or not state['enabled']:
            return
            
        try:
            net = self.net_resolver.get_connected_pins("esp32", f"GPIO{pin}")
        except Exception:
            return
            
        if not net:
            return
            
        duty_norm = state['duty'] / 1023.0
        freq = state['freq']
        
        # VERY IMPORTANT: Notify GPIO Manager so the UI catches it (oscilloscope, visual updates)
        self.gpio_manager.set_pwm(pin, freq, state['duty'])
        
        # Fire events to devices on the net
        for comp_id, pin_name in net:
            if comp_id in self.device_models:
                dev = self.device_models[comp_id]
                if hasattr(dev, "set_pwm"):
                    dev.set_pwm(freq, duty_norm)
                    
                    # Notify UI via event bus (using device_state_changed or similar)
                    try:
                        from esp32_lab.app.event_bus import get_event_bus
                        if hasattr(dev, "get_state_dict"):
                            get_event_bus().device_state_changed.emit(comp_id, dev.get_state_dict())
                    except Exception:
                        pass
