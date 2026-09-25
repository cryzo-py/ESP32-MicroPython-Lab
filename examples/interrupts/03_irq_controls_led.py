# 03_irq_controls_led.py — Bouton IRQ contrôle une LED
# IRQ sur GPIO27 → allume/éteint GPIO25

from machine import Pin
import time

button = Pin(27, Pin.IN, Pin.PULL_UP)
led    = Pin(25, Pin.OUT)

led_state = [0]

def toggle_led(pin):
    led_state[0] ^= 1
    led.value(led_state[0])
    print("LED:", "ON" if led_state[0] else "OFF")

button.irq(trigger=Pin.IRQ_FALLING, handler=toggle_led)

print("Appuyez sur le bouton (GPIO27) pour basculer la LED (GPIO25)")
while True:
    time.sleep_ms(100)
