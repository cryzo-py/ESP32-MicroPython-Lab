# 04_timer_servo.py - Balayage de Servo via un Timer
# Change la position (PWM) périodiquement sans bloquer

from machine import Pin, PWM, Timer
import time

servo = PWM(Pin(25), freq=50)

# Valeurs approx de rapport cyclique (duty) pour 0 et 180 degrés
POS_MIN = 26
POS_MAX = 128

current_pos = POS_MIN
step = 10

def update_servo(timer):
    global current_pos, step
    current_pos += step
    
    if current_pos >= POS_MAX:
        current_pos = POS_MAX
        step = -step
    elif current_pos <= POS_MIN:
        current_pos = POS_MIN
        step = -step
        
    servo.duty(current_pos)
    print("Servo position (duty):", current_pos)

tim = Timer(2)
tim.init(period=100, mode=Timer.PERIODIC, callback=update_servo)

print("Balayage automatique du Servo sur GPIO25...")
while True:
    time.sleep_ms(1000)
