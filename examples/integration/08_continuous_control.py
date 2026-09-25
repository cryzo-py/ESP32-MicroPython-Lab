from machine import Pin, ADC, PWM
import time

button = Pin(27, Pin.IN, Pin.PULL_UP)
adc = ADC(Pin(34))
led = PWM(Pin(25))
led.freq(1000)

while True:
    value = adc.read()
    if button.value() == 0:
        led.duty(value // 4)
    else:
        led.duty(0)
    time.sleep_ms(50)
