# 05_multiple_interrupts.py — Plusieurs GPIO IRQ indépendants
# GPIO27, GPIO26, GPIO32 ont chacun leur propre callback

from machine import Pin
import time

btn_a = Pin(27, Pin.IN, Pin.PULL_UP)
btn_b = Pin(26, Pin.IN, Pin.PULL_UP)
btn_c = Pin(32, Pin.IN, Pin.PULL_UP)

count = [0, 0, 0]

def on_a(pin):
    count[0] += 1
    print(f"IRQ-A (GPIO27) pression #{count[0]}")

def on_b(pin):
    count[1] += 1
    print(f"IRQ-B (GPIO26) pression #{count[1]}")

def on_c(pin):
    count[2] += 1
    print(f"IRQ-C (GPIO32) pression #{count[2]}")

btn_a.irq(trigger=Pin.IRQ_FALLING, handler=on_a)
btn_b.irq(trigger=Pin.IRQ_FALLING, handler=on_b)
btn_c.irq(trigger=Pin.IRQ_FALLING, handler=on_c)

print("3 boutons indépendants sur GPIO27, GPIO26, GPIO32")
while True:
    time.sleep_ms(100)
