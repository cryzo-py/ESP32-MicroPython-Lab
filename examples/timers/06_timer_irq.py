# 06_timer_irq.py - Un Timer déclenche un changement d'état GPIO
# Le changement de GPIO déclenche ensuite une interruption matérielle (IRQ)

from machine import Pin, Timer
import time

# GPIO25 configuré en sortie
out_pin = Pin(25, Pin.OUT)

# GPIO27 configuré en entrée avec IRQ
in_pin = Pin(27, Pin.IN)

def on_gpio_irq(pin):
    print(f"IRQ Détectée ! GPIO27 = {pin.value()}")

# L'IRQ se déclenche sur n'importe quel flanc
in_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=on_gpio_irq)

out_state = 0
def toggle_output(timer):
    global out_state
    out_state = not out_state
    print(f"Timer: basculement GPIO25 vers {int(out_state)}")
    out_pin.value(out_state)

# Timer pour basculer la broche de sortie toutes les 1000ms
tim = Timer(0)
tim.init(period=1000, mode=Timer.PERIODIC, callback=toggle_output)

print("Connectez physiquement (sur la breadboard) GPIO25 à GPIO27.")
print("Le Timer bascule GPIO25 -> se propage via le fil vers GPIO27 -> déclenche l'IRQ.")

while True:
    time.sleep_ms(100)
