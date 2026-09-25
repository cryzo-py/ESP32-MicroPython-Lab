from machine import Pin

button = Pin(27, Pin.IN, Pin.PULL_UP)
led = Pin(25, Pin.OUT)

while True:
    if button.value() == 0:
        led.value(1)
    else:
        led.value(0)
