
class LEDModel:
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.brightness = 0.0
        self.state = 'OFF' # OFF, ON, PWM
        
    def set_pwm(self, frequency: int, duty_normalized: float):
        if duty_normalized <= 0:
            self.state = 'OFF'
            self.brightness = 0.0
        elif duty_normalized >= 1.0:
            self.state = 'ON'
            self.brightness = 1.0
        else:
            self.state = 'PWM'
            self.brightness = duty_normalized

    def set_digital(self, value: bool):
        if value:
            self.state = 'ON'
            self.brightness = 1.0
        else:
            self.state = 'OFF'
            self.brightness = 0.0
