# 08_uart_hot_disconnect.py - Déconnexion à chaud
# Lancez le script, puis arrachez le jumper entre TX et RX en pleine exécution.

from machine import UART
import time

uart = UART(1, baudrate=115200, tx=17, rx=16)

count = 0
while True:
    count += 1
    # Envoi
    uart.write(f"Data {count}\n".encode('utf-8'))
    
    time.sleep_ms(200) # Laisse le temps au signal d'arriver
    
    # Lecture
    if uart.any():
        print(f"Reçu {uart.any()} bytes:", uart.read())
    else:
        print("Liaison interrompue ! TX non connecté à RX.")
        
    time.sleep_ms(1000)
