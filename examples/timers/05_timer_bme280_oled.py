# 05_timer_bme280_oled.py - Mise à jour asynchrone d'écran I2C
# Lit le BME280 et met à jour l'écran SSD1306 périodiquement

from machine import Pin, I2C, Timer
import time
import ssd1306
import bme280

i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Initialisation
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
bme = bme280.BME280(i2c=i2c)

def update_display(timer):
    # Lecture capteur
    t, p, h = bme.read_compensated_data()
    temp_c = t / 100.0
    hum = h / 1024.0
    
    # Affichage
    oled.fill(0)
    oled.text("ESP32 Station", 0, 0)
    oled.text(f"Temp: {temp_c:.1f} C", 0, 20)
    oled.text(f"Hum:  {hum:.1f} %", 0, 35)
    oled.show()
    
    print(f"Update: {temp_c:.1f}C, {hum:.1f}%")

# Lance la mise à jour toutes les 2 secondes
tim = Timer(0)
tim.init(period=2000, mode=Timer.PERIODIC, callback=update_display)

print("Système démarré. Mise à jour OLED via Timer.")
while True:
    time.sleep_ms(1000)
