from machine import ADC, Pin

adc = ADC(Pin(34))
led = Pin(25, Pin.OUT)

while True:
    value = adc.read()
    if value > 2048:
        led.value(1)
    else:
        led.value(0)
