# 01_button_irq.py — Interrupt déclenché par appui bouton
# GPIO27 avec PULL_UP. Quand le bouton est pressé: HIGH → LOW → IRQ_FALLING

from machine import Pin
import time

button = Pin(27, Pin.IN, Pin.PULL_UP)

def button_pressed(pin):
    print("Bouton pressé ! GPIO:", pin.value())

button.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed)

print("En attente d'interruption (IRQ_FALLING sur GPIO27)...")
while True:
    time.sleep_ms(100)
