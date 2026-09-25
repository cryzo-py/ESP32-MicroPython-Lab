from machine import Pin, PWM
import time

# Configure le PWM sur le GPIO25 à 50Hz (période 20ms)
servo = PWM(Pin(25), freq=50)

# Pour un servo 50Hz :
# 0°   (0.5ms) = ~26 duty_u16? Non, duty() (0-1023). 2.5% = 25.5 -> 26
# 90°  (1.5ms) = ~76 duty_u16? 7.5% = 76.7 -> 77
# 180° (2.5ms) = ~127 duty_u16? 12.5% = 127.8 -> 128

while True:
    print("0°")
    servo.duty(26)
    time.sleep(1)
    
    print("90°")
    servo.duty(77)
    time.sleep(1)
    
    print("180°")
    servo.duty(128)
    time.sleep(1)
