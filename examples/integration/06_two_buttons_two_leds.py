from machine import Pin

b1 = Pin(27, Pin.IN, Pin.PULL_UP)
b2 = Pin(26, Pin.IN, Pin.PULL_UP)
l1 = Pin(25, Pin.OUT)
l2 = Pin(33, Pin.OUT)

while True:
    l1.value(0 if b1.value() else 1)
    l2.value(0 if b2.value() else 1)
