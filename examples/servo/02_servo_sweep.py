from machine import Pin, PWM
import time

servo = PWM(Pin(25), freq=50)

while True:
    # 0 à 180°
    for duty in range(26, 129):
        servo.duty(duty)
        time.sleep(0.02)
        
    # 180° à 0°
    for duty in range(128, 25, -1):
        servo.duty(duty)
        time.sleep(0.02)
