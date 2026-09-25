# 02_uart_terminal.py - Communication avec un Terminal Virtuel
#
# Prérequis :
# 1. Ajoutez un Virtual UART Terminal sur l'interface
# 2. Connectez TX (Pin 17) de l'ESP32 au RX du terminal
# 3. Connectez RX (Pin 16) de l'ESP32 au TX du terminal

from machine import UART
import time

uart = UART(1, baudrate=9600, tx=17, rx=16)

count = 0
while True:
    count += 1
    # Envoi vers le terminal
    uart.write(f"Ping {count}\n".encode('utf-8'))
    
    # Lecture depuis le terminal (si vous injectez des données)
    if uart.any():
        data = uart.read()
        print("Reçu du terminal:", data.decode('utf-8'))
        
    time.sleep_ms(1000)
