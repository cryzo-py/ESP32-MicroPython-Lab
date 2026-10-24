"""
Gestionnaire des broches GPIO pour la simulation ESP32
"""

from typing import Callable
from enum import IntEnum


class GPIOMode(IntEnum):
    IN = 1
    OUT = 3
    OPEN_DRAIN = 7


class GPIOPull(IntEnum):
    PULL_NONE = 0
    PULL_UP = 1
    PULL_DOWN = 2


class GPIOManager:
    """Gère l'état logique des GPIO de la carte virtuelle (ESP32, Arduino Uno, etc.)"""
    def __init__(self, board_profile=None):
        from ..core.board_profiles import load_board_profile, BoardProfile
        if board_profile is None:
            try:
                self.board_profile = load_board_profile("esp32_wroom_32")
            except Exception:
                self.board_profile = None
        else:
            self.board_profile = board_profile

        self._modes: dict[int, GPIOMode] = {}
        self._pulls: dict[int, GPIOPull] = {}
        self._values: dict[int, int] = {}
        self._adc_values: dict[int, int] = {}
        self._pwm_values: dict[int, tuple[int, int]] = {} # (freq, duty)
        self._listeners: list[Callable[[int, int], None]] = []
        self._adc_listeners: list[Callable[[int, int], None]] = []
        self._pwm_listeners: list[Callable[[int, int, int], None]] = []

    def set_board_profile(self, profile) -> None:
        self.board_profile = profile

    def configure(self, pin: int, mode: int, pull: int = GPIOPull.PULL_NONE) -> None:
        if self.board_profile:
            pin_def = self.board_profile.get_pin(pin)
            if not pin_def:
                raise ValueError(f"GPIO {pin} invalide ou non supporté par ce profil de carte.")
            from ..core.board_profiles.board_profile import BoardPinType
            if pin_def.pin_type in (BoardPinType.POWER, BoardPinType.GROUND):
                raise ValueError(f"La broche {pin} est une alimentation, pas un GPIO.")
            if pin_def.pin_type == BoardPinType.INPUT_ONLY and mode == 3: # 3 = OUT
                raise ValueError(f"GPIO {pin} est input-only et ne peut pas être configuré en sortie.")
            if pull != 0 and not getattr(pin_def, "pull_up_down", True):
                raise ValueError(f"GPIO {pin} ne supporte pas les résistances de tirage (pull-up/pull-down).")
        else:
            from ..core.models.board import create_default_esp32_wroom, PinType
            board = create_default_esp32_wroom()
            pin_def = board.get_pin(pin)
            if not pin_def:
                raise ValueError(f"GPIO {pin} invalide ou non supporté par ce profil de carte.")
            if pin_def.pin_type in (PinType.POWER, PinType.GROUND):
                raise ValueError(f"La broche {pin} est une alimentation, pas un GPIO.")
            if pin_def.pin_type == PinType.INPUT_ONLY and mode == 3: # 3 = OUT
                raise ValueError(f"GPIO {pin} est input-only et ne peut pas être configuré en sortie.")
            if pull != 0 and not pin_def.pull_up_down:
                raise ValueError(f"GPIO {pin} ne supporte pas les résistances de tirage (pull-up/pull-down).")
            
        self._modes[pin] = GPIOMode(mode)
        self._pulls[pin] = GPIOPull(pull)
        if pin not in self._values:
            if mode == GPIOMode.IN and pull == GPIOPull.PULL_UP:
                self._values[pin] = 1
            else:
                self._values[pin] = 0

    def set_mode(self, pin: int, mode: int, pull: int = GPIOPull.PULL_NONE) -> None:
        self.configure(pin, mode, pull)

    def get_mode(self, pin: int) -> GPIOMode:
        return self._modes.get(pin, GPIOMode.IN)

    def write(self, pin: int, value: int) -> None:
        val = 1 if value else 0
        old_val = self._values.get(pin)
        self._values[pin] = val
        if old_val != val:
            self._notify(pin, val)
            # Phase 5.11: propagate the new output value to any INPUT GPIO connected
            # via the electrical topology, so IRQ listeners see the transition.
            self._propagate_to_inputs(pin, val)

    def _get_pin_net(self, pin: int) -> list:
        if not getattr(self, 'net_resolver', None):
            return []
        board_comp = getattr(self.board_profile, "component_type", "esp32") if self.board_profile else "esp32"
        comp_candidates = [board_comp] if board_comp == "esp32" else [board_comp, "esp32"]
        pin_variants = [f"GPIO{pin}", f"D{pin}", str(pin)]
        if self.board_profile:
            pin_obj = self.board_profile.get_pin(pin)
            if pin_obj and pin_obj.name and pin_obj.name not in pin_variants:
                pin_variants.insert(0, pin_obj.name)

        fallback_net = None
        for cid in comp_candidates:
            for pvar in pin_variants:
                try:
                    net = self.net_resolver.get_connected_pins(cid, pvar)
                    if net:
                        if len(net) > 1:
                            return net
                        if fallback_net is None:
                            fallback_net = net
                except Exception:
                    pass
        return fallback_net or []

    def _parse_pin_number(self, p_id: str) -> int | None:
        if p_id.startswith("GPIO") and p_id[4:].isdigit():
            return int(p_id[4:])
        if p_id.startswith("D") and p_id[1:].isdigit():
            return int(p_id[1:])
        if p_id.isdigit():
            return int(p_id)
        if self.board_profile:
            p_obj = self.board_profile.get_pin(p_id)
            if p_obj and p_obj.number >= 0:
                return p_obj.number
        return None

    def _propagate_to_inputs(self, output_pin: int, output_val: int) -> None:
        """
        When an OUTPUT pin changes, re-evaluate all INPUT GPIOs electrically
        connected on the same net. If their resolved logical value changed,
        fire _notify so that IRQ listeners (and other observers) see the edge.
        """
        net = self._get_pin_net(output_pin)
        if not net:
            return

        board_comps = {"esp32", "arduino_uno"}
        if self.board_profile:
            board_comps.add(self.board_profile.component_type)

        for comp_id, pin_name in net:
            if comp_id not in board_comps:
                continue
            other_pin = self._parse_pin_number(pin_name)
            if other_pin is None or other_pin == output_pin:
                continue
            if self._modes.get(other_pin) == GPIOMode.IN:
                resolved = self.read(other_pin)
                old = self._values.get(other_pin)
                if old != resolved:
                    self._values[other_pin] = resolved
                    self._notify(other_pin, resolved)

    def set_pin_state(self, pin: int, value: int) -> None:
        self.write(pin, value)

    def get_net_state(self, pin: int):
        from ..simulator.models.digital import DigitalState
        
        mode = self._modes.get(pin)
        
        vcc = False
        gnd = False
        high_outputs = 0
        low_outputs = 0
        
        # Determine internal pull
        pull = self._pulls.get(pin, GPIOPull.PULL_NONE)
        pull_high = (pull == GPIOPull.PULL_UP)
        pull_low = (pull == GPIOPull.PULL_DOWN)

        net = self._get_pin_net(pin)
        if net:
            board_comps = {"esp32", "arduino_uno"}
            if self.board_profile:
                board_comps.add(self.board_profile.component_type)

            for comp_id, p_id in net:
                if comp_id in board_comps:
                    if p_id in ("3V3", "VIN", "VCC", "5V", "IOREF"):
                        vcc = True
                    elif "GND" in p_id:
                        gnd = True
                    else:
                        other_pin = self._parse_pin_number(p_id)
                        if other_pin is not None and self._modes.get(other_pin) == GPIOMode.OUT:
                            val = self._values.get(other_pin, 0)
                            if val == 1:
                                high_outputs += 1
                            else:
                                low_outputs += 1
                elif hasattr(self, "device_models") and comp_id in self.device_models:
                    # Also check if external devices drive the net
                    dev = self.device_models[comp_id]
                    if hasattr(dev, "get_digital_state"):
                        d_state = dev.get_digital_state(p_id)
                        if d_state and d_state.status == 'HIGH':
                            high_outputs += 1
                        elif d_state and d_state.status == 'LOW':
                            low_outputs += 1
                
        is_high = vcc or high_outputs > 0
        is_low = gnd or low_outputs > 0
        
        if is_high and is_low:
            return DigitalState(value=0, status='CONFLICT')
        elif is_high:
            return DigitalState(value=1, status='HIGH')
        elif is_low:
            return DigitalState(value=0, status='LOW')
            
        if pull_high:
            return DigitalState(value=1, status='PULL_UP')
        elif pull_low:
            return DigitalState(value=0, status='PULL_DOWN')
            
        return DigitalState(value=0, status='FLOATING')

    def read(self, pin: int) -> int:
        mode = self._modes.get(pin)
        if mode == GPIOMode.OUT:
            return self._values.get(pin, 0)
            
        state = self.get_net_state(pin)
        if state.status == 'CONFLICT':
            print(f"Warning: GPIO{pin} read detected CONFLICT on net! Returning 0.")
            return 0
        return state.value

    def get_pin_state(self, pin: int) -> int:
        return self.read(pin)

    def set_adc_value(self, pin: int, value: int) -> None:
        max_adc = getattr(self.board_profile, "adc_resolution", 4095) if self.board_profile else 4095
        val = max(0, min(max_adc, int(value)))
        self._adc_values[pin] = val
        for cb in self._adc_listeners:
            try:
                cb(pin, val)
            except Exception:
                pass

    def read_adc(self, pin: int) -> int:
        return self._adc_values.get(pin, 0)

    def set_pwm(self, pin: int, freq: int, duty: int) -> None:
        self._pwm_values[pin] = (freq, duty)
        for cb in self._pwm_listeners:
            try:
                cb(pin, freq, duty)
            except Exception:
                pass

    def add_adc_listener(self, callback: Callable[[int, int], None]) -> None:
        if callback not in self._adc_listeners:
            self._adc_listeners.append(callback)

    def add_pwm_listener(self, callback: Callable[[int, int, int], None]) -> None:
        if callback not in self._pwm_listeners:
            self._pwm_listeners.append(callback)

    def set_external_input(self, pin: int, value: int) -> None:
        """Modifie la valeur d'une broche depuis un composant extérieur (ex: bouton appuyé)"""
        val = 1 if value else 0
        self._values[pin] = val
        self._notify(pin, val)

    def add_listener(self, callback: Callable[[int, int], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[int, int], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self, pin: int, value: int) -> None:
        for callback in self._listeners:
            try:
                callback(pin, value)
            except Exception:
                pass

    def reset(self) -> None:
        self._modes.clear()
        self._pulls.clear()
        self._values.clear()
        self._adc_values.clear()
        self._pwm_values.clear()
        
        # Priority 3: State Leakage
        from .modules import machine as sim_machine
        # Removed I2C global reset because it's now handled by engine
        if sim_machine.Pin._gpio_manager == self:
            sim_machine.Pin._gpio_manager = None
        
        try:
            from .modules import hcsr04
            hcsr04._hcsr04_distances.clear()
        except Exception:
            pass
