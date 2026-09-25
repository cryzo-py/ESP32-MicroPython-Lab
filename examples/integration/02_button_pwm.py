from machine import Pin, PWM

button = Pin(27, Pin.IN, Pin.PULL_UP)

led = PWM(Pin(25))
led.freq(1000)

while True:
    if button.value() == 0:
        led.duty(1023)
    else:
        led.duty(0)
