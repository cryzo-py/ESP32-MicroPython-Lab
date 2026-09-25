# 07_uart_two_channels.py - Utilisation de UART1 et UART2 simultanément
#
# Prérequis :
# Connectez TX1 (17) -> RX2 (5)
# Connectez TX2 (4)  -> RX1 (16)

from machine import UART
import time

uart1 = UART(1, baudrate=115200, tx=17, rx=16)
uart2 = UART(2, baudrate=115200, tx=4, rx=5)

uart1.write(b"Message de UART1 vers UART2")
time.sleep_ms(50)

if uart2.any():
    print("UART2 a reçu:", uart2.read())

uart2.write(b"Accuse de reception de UART2")
time.sleep_ms(50)

if uart1.any():
    print("UART1 a reçu:", uart1.read())
