# 06_uart_timer.py - UART via Timer (Non-bloquant)
# Envoi de données périodiques par Timer

from machine import UART, Timer
import time

uart = UART(1, baudrate=115200, tx=17, rx=16)

def send_ping(timer):
    uart.write(b"PING!\n")
    print("Envoyé PING!")

timer = Timer(0)
timer.init(period=2000, mode=Timer.PERIODIC, callback=send_ping)

while True:
    if uart.any():
        print("Reçu:", uart.read())
    time.sleep_ms(100)
