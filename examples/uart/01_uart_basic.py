# 01_uart_basic.py - Test basique d'initialisation UART
from machine import UART

# Initialisation du canal UART 1 (TX=17, RX=16 par convention souvent utilisée)
uart = UART(1, baudrate=115200, tx=17, rx=16)

# Envoi de données basiques
# S'il n'y a pas de périphérique connecté, les données sont "perdues" (comme en réalité)
uart.write(b"HELLO UART\n")

print("Données envoyées sur UART1 (TX=17).")
