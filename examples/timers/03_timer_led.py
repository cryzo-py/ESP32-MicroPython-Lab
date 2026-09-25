# 03_timer_led.py - Faire clignoter une LED avec un Timer
# Utilise un Timer périodique pour basculer l'état de GPIO25

from machine import Pin, Timer
import time

led = Pin(25, Pin.OUT)
led_state = 0

def toggle_led(timer):
    global led_state
    led_state = not led_state
    led.value(led_state)
    print("LED", "ON" if led_state else "OFF")

tim = Timer(0)
tim.init(period=500, mode=Timer.PERIODIC, callback=toggle_led)

print("Clignotement de la LED sur GPIO25 toutes les 500ms...")
while True:
    time.sleep_ms(1000)
