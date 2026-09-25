# 05_uart_echo.py - Répéteur UART
# Tout ce qui est reçu est immédiatement renvoyé

from machine import UART

uart = UART(1, baudrate=115200, tx=17, rx=16)

print("Serveur Echo Démarré. En attente de données...")
while True:
    if uart.any():
        data = uart.read()
        if data:
            print("Echoing:", data)
            uart.write(data)
