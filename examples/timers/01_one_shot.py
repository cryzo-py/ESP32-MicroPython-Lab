# 01_one_shot.py - Exemple de Timer One-Shot
# Exécute un callback une seule fois après un délai défini.

from machine import Timer
import time

def on_timer(timer):
    print("Timer One-Shot déclenché !", timer)

# Initialisation du Timer 0
tim = Timer(0)

print("Démarrage du timer (2000 ms)...")
tim.init(period=2000, mode=Timer.ONE_SHOT, callback=on_timer)

# Le programme principal continue sans bloquer
while True:
    print("Boucle principale en cours...")
    time.sleep_ms(500)
