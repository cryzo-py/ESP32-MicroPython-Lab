from machine import Pin
import time

pin_out = Pin(25, Pin.OUT)
pin_in = Pin(27, Pin.IN)

while True:
    pin_out.value(1)
    time.sleep_ms(100)
    print("Read IN when OUT=1 :", pin_in.value())
    
    pin_out.value(0)
    time.sleep_ms(100)
    print("Read IN when OUT=0 :", pin_in.value())
