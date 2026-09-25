# 02_periodic.py - Exemple de Timer Périodique
# Exécute un callback à intervalles réguliers.

from machine import Timer
import time

count = 0

def on_timer(timer):
    global count
    count += 1
    print(f"Tick ! (Compteur = {count})")
    
    if count >= 10:
        print("Désactivation du timer.")
        timer.deinit()

tim = Timer(1)
print("Démarrage du timer périodique (1000 ms)...")
tim.init(period=1000, mode=Timer.PERIODIC, callback=on_timer)

while True:
    time.sleep_ms(2000)
    if count < 10:
        print("  ... la boucle principale n'est pas bloquée")
