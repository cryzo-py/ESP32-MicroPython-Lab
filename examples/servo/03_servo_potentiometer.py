from machine import Pin, ADC, PWM
import time

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB) # 0-3.3V, valeurs 0-4095

servo = PWM(Pin(25), freq=50)

while True:
    val = pot.read() # 0-4095
    
    # Map 0-4095 to 26-128
    duty = 26 + int((val / 4095.0) * (128 - 26))
    
    servo.duty(duty)
    time.sleep(0.05)
