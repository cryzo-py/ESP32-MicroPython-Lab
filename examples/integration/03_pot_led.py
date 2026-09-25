from machine import ADC, Pin, PWM

adc = ADC(Pin(34))
led = PWM(Pin(25))
led.freq(1000)

while True:
    value = adc.read()
    led.duty(value // 4)
