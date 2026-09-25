
from ..models.analog import AnalogState

class PotentiometerModel:
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.position = 0.5  # 0.0 to 1.0

    def get_analog_state(self, pin_name: str) -> AnalogState:
        if pin_name == "sig":
            val = int(self.position * 4095)
            return AnalogState(value=val, status="VALUE")
        return AnalogState(value=None, status="FLOATING")
