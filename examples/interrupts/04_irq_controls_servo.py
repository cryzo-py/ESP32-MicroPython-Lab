# 04_irq_controls_servo.py — Bouton IRQ → PWM → Servo
# Démontre la chaîne complète : PHYSICAL INPUT → IRQ → MicroPython → PWM → Servo

from machine import Pin, PWM
import time

button = Pin(27, Pin.IN, Pin.PULL_UP)
servo  = PWM(Pin(25), freq=50)

# Positions du servo (duty 0-1023 pour 50Hz)
POS_A = 26   # ~0°   (0.5ms)
POS_B = 128  # ~180° (2.5ms)

current_pos = [POS_A]

def on_button(pin):
    # Toggle entre les deux positions
    if current_pos[0] == POS_A:
        current_pos[0] = POS_B
        print("Servo → 180°")
    else:
        current_pos[0] = POS_A
        print("Servo → 0°")
    servo.duty(current_pos[0])

# Positionner à 0° au démarrage
servo.duty(POS_A)

button.irq(trigger=Pin.IRQ_FALLING, handler=on_button)

print("Chaîne: Bouton(GPIO27) → IRQ → PWM(GPIO25) → Servo")
while True:
    time.sleep_ms(100)
