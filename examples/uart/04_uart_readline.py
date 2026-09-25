# 04_uart_readline.py - Lecture par ligne
# Utile pour les capteurs GPS ou série basés sur des trames terminées par \n

from machine import UART
import time

uart = UART(1, baudrate=115200, tx=17, rx=16)

# Simulation d'envoi par blocs (loopback TX->RX requis)
uart.write(b"Line 1\nLine ")
time.sleep_ms(10)
uart.write(b"2\nIncomplete Line...")

print("Lecture ligne 1:", uart.readline()) # b'Line 1\n'
print("Lecture ligne 2:", uart.readline()) # b'Line 2\n'
print("Lecture reste:", uart.readline())   # None (pas de \n)
print("Tout lire:", uart.read())           # b'Incomplete Line...'
