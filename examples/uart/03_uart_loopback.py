# 03_uart_loopback.py - Test de bouclage matériel
#
# Prérequis :
# Connectez physiquement la broche TX (17) à la broche RX (16) 
# à l'aide d'un fil (jumper) sur la breadboard.

from machine import UART
import time

uart = UART(1, baudrate=115200, tx=17, rx=16)

# On envoie "ECHO_TEST"
uart.write(b"ECHO_TEST\n")

# On attend un peu que l'octet traverse le fil
time.sleep_ms(100)

# On vérifie si la donnée est revenue sur RX
if uart.any():
    data = uart.read()
    print("Succès loopback, reçu:", data)
else:
    print("Erreur: RX n'a rien reçu. Avez-vous connecté TX à RX ?")
