from machine import ADC, Pin, PWM

adc1 = ADC(Pin(34))
adc2 = ADC(Pin(35))
pwm1 = PWM(Pin(25))
pwm2 = PWM(Pin(26))

while True:
    v1 = adc1.read()
    v2 = adc2.read()
    pwm1.duty(v1 // 4)
    pwm2.duty(v2 // 4)
