# 02_rising_falling.py — Détection front montant ET descendant
# Démontre IRQ_RISING et IRQ_FALLING sur la même broche

from machine import Pin
import time

button = Pin(27, Pin.IN, Pin.PULL_UP)

def on_edge(pin):
    val = pin.value()
    if val == 0:
        print("FALLING (bouton pressé)  GPIO27 =", val)
    else:
        print("RISING  (bouton relâché) GPIO27 =", val)

# IRQ_RISING | IRQ_FALLING (= Pin.IRQ_ANY_EDGE)
button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=on_edge)

print("Surveillance IRQ_RISING + IRQ_FALLING sur GPIO27...")
while True:
    time.sleep_ms(50)
