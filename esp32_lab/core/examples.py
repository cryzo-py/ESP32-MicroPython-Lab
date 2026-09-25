"""
Bibliothèque de projets et d'exemples pré-câblés pour ESP32 MicroPython Lab
"""

from .models.component import ComponentModel, ComponentPin
from .models.connection import ConnectionModel
from .models.project import ProjectModel


def get_all_examples() -> dict[str, ProjectModel]:
    return {
        "blink": create_blink_example(),
        "button_led": create_button_led_example(),
        "pot_pwm": create_pot_pwm_example(),
        "servo_sweep": create_servo_example(),
        "dht22_weather": create_dht22_example(),
        "oled_display": create_oled_example(),
        "hcsr04_sonar": create_hcsr04_example(),
        "lcd_display": create_lcd_example(),
        "relay_control": create_relay_example(),
        "neopixel_ring": create_neopixel_example(),
        "wifi_web_server": create_wifi_example(),
        "ble_beacon": create_ble_example(),
        "weather_cloud_iot": create_weather_iot_example(),
        "wifi_scanner": create_wifi_scanner_example(),
        "mqtt_client": create_mqtt_example(),
        "ble_scanner": create_ble_scanner_example(),
    }


def create_blink_example() -> ProjectModel:
    code = """# Exemple 1 : Clignotement d'une LED
from machine import Pin
from time import sleep

led = Pin(2, Pin.OUT)
print("Démarrage du clignotement...")

while True:
    led.value(1)
    print("LED ALLUMÉE")
    sleep(1)
    led.value(0)
    print("LED ÉTEINTE")
    sleep(1)
"""
    proj = ProjectModel(name="LED Clignotante", description="Clignotement simple sur GPIO 2 via platine de montage", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=280, y=50)
    # Composants posés directement dans les alvéoles de la platine
    led = ComponentModel(id="led_1", type="led", x=334.5, y=129.0, properties={"color": "red"}, pin_insertions={"anode": "r10_b", "cathode": "r11_b"})
    res = ComponentModel(id="res_1", type="resistor", x=343.0, y=188.5, properties={"value": 220}, pin_insertions={"pin1": "r11_c", "pin2": "r17_c"})
    proj.components.extend([breadboard, led, res])
    
    proj.connections.extend([
        # Cavalier ESP32 GPIO2 -> Ligne 10 de la platine
        ConnectionModel(id="w1", from_component="esp32", from_pin="GPIO2", to_component="breadboard_1", to_pin="r10_a", color="#ef4444"),
        # Cavalier interne : Ligne 17 vers rail de masse
        ConnectionModel(id="w2", from_component="breadboard_1", from_pin="r17_a", to_component="breadboard_1", to_pin="rail_l_minus_17", color="#1e293b"),
        # Cavalier de masse : rail GND -> ESP32 GND
        ConnectionModel(id="w3", from_component="breadboard_1", from_pin="rail_l_minus_28", to_component="esp32", to_pin="GND_1", color="#0f172a"),
    ])
    return proj


def create_button_led_example() -> ProjectModel:
    code = """# Exemple 2 : Bouton poussoir contrôlant une LED
from machine import Pin
from time import sleep

led = Pin(2, Pin.OUT)
bouton = Pin(4, Pin.IN, Pin.PULL_DOWN)

print("Appuyez sur le bouton virtuel pour allumer la LED...")

while True:
    if bouton.value() == 1:
        led.value(1)
        print("Bouton pressé -> LED ON")
    else:
        led.value(0)
    sleep(0.1)
"""
    proj = ProjectModel(name="Bouton poussoir et LED", description="Contrôle d'une LED par bouton poussoir monté sur platine", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=280, y=50)
    led = ComponentModel(id="led_1", type="led", x=334.5, y=112.0, properties={"color": "green"}, pin_insertions={"anode": "r8_b", "cathode": "r9_b"})
    btn = ComponentModel(id="btn_1", type="button", x=379.0, y=214.0, pin_insertions={"pin1": "r16_e", "pin2": "r16_f", "pin3": "r18_e", "pin4": "r18_f"})
    proj.components.extend([breadboard, led, btn])
    
    proj.connections.extend([
        # ESP32 GPIO2 -> row 8 (LED anode strip)
        ConnectionModel(id="w1", from_component="esp32", from_pin="GPIO2", to_component="breadboard_1", to_pin="r8_a", color="#22c55e"),
        # LED cathode strip (row 9) -> GND rail
        ConnectionModel(id="w2", from_component="breadboard_1", from_pin="r9_a", to_component="breadboard_1", to_pin="rail_l_minus_9", color="#0f172a"),
        # ESP32 GPIO4 -> row 16 (button pin1 strip, left side)
        ConnectionModel(id="w3", from_component="esp32", from_pin="GPIO4", to_component="breadboard_1", to_pin="r16_a", color="#38bdf8"),
        # Button pin4 strip (row 18 right) -> VCC rail
        ConnectionModel(id="w4", from_component="breadboard_1", from_pin="r18_g", to_component="breadboard_1", to_pin="rail_l_plus_18", color="#ef4444"),
        # 3.3V -> VCC rail
        ConnectionModel(id="w5", from_component="esp32", from_pin="3V3", to_component="breadboard_1", to_pin="rail_l_plus_5", color="#dc2626"),
        # GND rail -> ESP32 GND
        ConnectionModel(id="w6", from_component="breadboard_1", from_pin="rail_l_minus_28", to_component="esp32", to_pin="GND_1", color="#0f172a"),
    ])
    return proj


def create_pot_pwm_example() -> ProjectModel:
    code = """# Exemple 3 : Gradateur de luminosité avec Potentiomètre et PWM
from machine import Pin, ADC, PWM
from time import sleep

pot = ADC(Pin(34))
led_pwm = PWM(Pin(2), freq=1000)

print("Tournez le potentiomètre avec la souris pour faire varier la luminosité...")

while True:
    val = pot.read() # 0 à 4095
    # Adapter la valeur ADC vers le PWM duty (0 à 1023)
    duty = int(val / 4)
    led_pwm.duty(duty)
    tension = val * 3.3 / 4095
    print(f"ADC: {val} | Tension: {tension:.2f}V | Duty: {duty}")
    sleep(0.2)
"""
    proj = ProjectModel(name="Variateur Potentiomètre & PWM", description="Lecture analogique ADC et modulation PWM", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=280, y=50)
    pot = ComponentModel(id="pot_1", type="potentiometer", x=330, y=100, properties={"raw_value": 2048})
    led = ComponentModel(id="led_1", type="led", x=330, y=210, properties={"color": "blue"})
    proj.components.extend([breadboard, pot, led])
    
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="esp32", from_pin="GPIO34", to_component="pot_1", to_pin="sig", color="#38bdf8"),
        ConnectionModel(id="w2", from_component="esp32", from_pin="3V3", to_component="pot_1", to_pin="vcc", color="#ef4444"),
        ConnectionModel(id="w3", from_component="esp32", from_pin="GND_1", to_component="pot_1", to_pin="gnd", color="#0f172a"),
        ConnectionModel(id="w4", from_component="esp32", from_pin="GPIO2", to_component="led_1", to_pin="anode", color="#3b82f6"),
        ConnectionModel(id="w5", from_component="led_1", from_pin="cathode", to_component="esp32", to_pin="GND_2", color="#0f172a"),
    ])
    return proj


def create_servo_example() -> ProjectModel:
    code = """# Exemple 4 : Balayage automatique d'un Servomoteur SG90
from machine import Pin, PWM
from time import sleep

# SG90 : PWM 50Hz, duty ~26 pour 0°, ~128 pour 180°
servo = PWM(Pin(18), freq=50)

def set_angle(angle):
    duty = int(26 + (angle / 180.0) * (128 - 26))
    servo.duty(duty)
    print(f"Angle du servomoteur : {angle}° (duty={duty})")

print("Démarrage du balayage du servomoteur...")

while True:
    for a in range(0, 181, 30):
        set_angle(a)
        sleep(0.4)
    for a in range(180, -1, -30):
        set_angle(a)
        sleep(0.4)
"""
    proj = ProjectModel(name="Balayage Servomoteur SG90", description="Contrôle d'angle d'un servomoteur en PWM 50Hz", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=280, y=50)
    servo = ComponentModel(id="servo_1", type="servo", x=330, y=140, properties={"angle": 0.0})
    proj.components.extend([breadboard, servo])
    
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="esp32", from_pin="GPIO18", to_component="servo_1", to_pin="sig", color="#f97316"),
        ConnectionModel(id="w2", from_component="esp32", from_pin="VIN", to_component="servo_1", to_pin="vcc", color="#ef4444"),
        ConnectionModel(id="w3", from_component="esp32", from_pin="GND_1", to_component="servo_1", to_pin="gnd", color="#0f172a"),
    ])
    return proj


def create_dht22_example() -> ProjectModel:
    code = """# Exemple 5 : Station Météo Capteur DHT22 (Température & Humidité)
from machine import Pin
from time import sleep
import dht

capteur = dht.DHT22(Pin(4))
print("Lecture de la station météo (DHT22 sur GPIO 4)...")

while True:
    try:
        capteur.measure()
        temp = capteur.temperature()
        hum = capteur.humidity()
        print(f"Température : {temp:.1f} °C | Humidité : {hum:.1f} %")
    except Exception as e:
        print(f"Erreur de lecture : {e}")
    sleep(2)
"""
    proj = ProjectModel(name="Station Météo DHT22", description="Lecture de capteur de température et d'humidité", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=280, y=50)
    dht_comp = ComponentModel(id="dht_1", type="dht22", x=330, y=130, properties={"temperature": 25.5, "humidity": 60.0, "connected_pin": 4})
    proj.components.extend([breadboard, dht_comp])
    
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="esp32", from_pin="3V3", to_component="dht_1", to_pin="vcc", color="#ef4444"),
        ConnectionModel(id="w2", from_component="esp32", from_pin="GPIO4", to_component="dht_1", to_pin="data", color="#38bdf8"),
        ConnectionModel(id="w3", from_component="esp32", from_pin="GND_1", to_component="dht_1", to_pin="gnd", color="#0f172a"),
    ])
    return proj


def create_oled_example() -> ProjectModel:
    code = """# Exemple 6 : Affichage graphique sur Écran OLED SSD1306 (I2C)
from machine import Pin, I2C
from time import sleep
import ssd1306

# Initialisation du bus I2C (SDA=GPIO21, SCL=GPIO22)
i2c = I2C(scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

print("Initialisation de l'écran OLED...")

count = 0
while True:
    oled.fill(0) # Effacer l'écran
    oled.rect(0, 0, 128, 64, 1) # Cadre extérieur
    oled.text("ESP32 LAB", 28, 8, 1)
    oled.line(10, 22, 118, 22, 1)
    oled.text(f"COMPTEUR: {count}", 16, 32, 1)
    oled.text("MICROPYTHON", 20, 48, 1)
    oled.show()
    
    print(f"Écran mis à jour : Compteur = {count}")
    count += 1
    sleep(1)
"""
    proj = ProjectModel(name="Écran OLED SSD1306", description="Graphismes et textes sur écran I2C 128x64", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=280, y=50)
    oled_comp = ComponentModel(id="oled_1", type="oled", x=330, y=140, properties={"width": 128, "height": 64})
    proj.components.extend([breadboard, oled_comp])
    
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="esp32", from_pin="GND_1", to_component="oled_1", to_pin="gnd", color="#0f172a"),
        ConnectionModel(id="w2", from_component="esp32", from_pin="3V3", to_component="oled_1", to_pin="vcc", color="#ef4444"),
        ConnectionModel(id="w3", from_component="esp32", from_pin="GPIO22", to_component="oled_1", to_pin="scl", color="#fbbf24"),
        ConnectionModel(id="w4", from_component="esp32", from_pin="GPIO21", to_component="oled_1", to_pin="sda", color="#34d399"),
    ])
    return proj


def create_hcsr04_example() -> ProjectModel:
    code = """# Exemple 7 : Télémètre à ultrasons HC-SR04
from machine import Pin
from time import sleep
from hcsr04 import HCSR04

# Trig sur GPIO 5, Echo sur GPIO 18
sensor = HCSR04(trigger_pin=5, echo_pin=18)
print("Démarrage du télémètre ultrasonique...")

while True:
    try:
        dist = sensor.distance_cm()
        print(f"Distance mesurée : {dist:.1f} cm")
    except Exception as e:
        print(f"Erreur de mesure : {e}")
    sleep(0.5)
"""
    proj = ProjectModel(name="Télémètre HC-SR04", description="Mesure de distance sans contact", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=280, y=50)
    sonar = ComponentModel(id="sonar_1", type="hcsr04", x=330, y=140, properties={"distance_cm": 35.0, "trig_pin": 5, "echo_pin": 18})
    proj.components.extend([breadboard, sonar])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="esp32", from_pin="5V", to_component="sonar_1", to_pin="vcc", color="#ef4444"),
        ConnectionModel(id="w2", from_component="esp32", from_pin="GPIO5", to_component="sonar_1", to_pin="trig", color="#3b82f6"),
        ConnectionModel(id="w3", from_component="esp32", from_pin="GPIO18", to_component="sonar_1", to_pin="echo", color="#10b981"),
        ConnectionModel(id="w4", from_component="esp32", from_pin="GND_1", to_component="sonar_1", to_pin="gnd", color="#0f172a"),
    ])
    return proj


def create_lcd_example() -> ProjectModel:
    code = """# Exemple 8 : Afficheur LCD 16x2 I2C
from machine import Pin, I2C
from time import sleep
from liquidcrystal_i2c import I2cLcd

# Bus I2C : SDA=GPIO21, SCL=GPIO22
i2c = I2C(scl=Pin(22), sda=Pin(21))
lcd = I2cLcd(i2c, 0x27, 2, 16)

lcd.clear()
lcd.putstr("ESP32 Lab\\nMicroPython !")

sec = 0
while True:
    lcd.move_to(0, 1)
    lcd.putstr(f"Temps: {sec}s     ")
    print(f"LCD mis à jour : {sec}s")
    sec += 1
    sleep(1)
"""
    proj = ProjectModel(name="Afficheur LCD 16x2", description="Affichage alphanumérique I2C", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=280, y=50)
    lcd = ComponentModel(id="lcd_1", type="lcd", x=330, y=140, properties={"lines": 2, "cols": 16})
    proj.components.extend([breadboard, lcd])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="esp32", from_pin="GND_1", to_component="lcd_1", to_pin="gnd", color="#0f172a"),
        ConnectionModel(id="w2", from_component="esp32", from_pin="5V", to_component="lcd_1", to_pin="vcc", color="#ef4444"),
        ConnectionModel(id="w3", from_component="esp32", from_pin="GPIO21", to_component="lcd_1", to_pin="sda", color="#34d399"),
        ConnectionModel(id="w4", from_component="esp32", from_pin="GPIO22", to_component="lcd_1", to_pin="scl", color="#fbbf24"),
    ])
    return proj


def create_relay_example() -> ProjectModel:
    code = """# Exemple 9 : Pilotage de puissance avec Module Relais 5V
from machine import Pin
from time import sleep

# Commande du relais sur le GPIO 19
relais = Pin(19, Pin.OUT)
print("Démarrage du cycle de commutation du relais...")

while True:
    print("Relais ACTIVÉ (Contact NO fermé)")
    relais.value(1)
    sleep(2)
    print("Relais DÉSACTIVÉ (Contact NC fermé)")
    relais.value(0)
    sleep(2)
"""
    proj = ProjectModel(name="Module Relais 5V", description="Commutation de puissance électromécanique", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=260, y=50)
    relay = ComponentModel(id="relay_1", type="relay", x=330, y=140)
    proj.components.extend([breadboard, relay])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="esp32", from_pin="5V", to_component="relay_1", to_pin="vcc", color="#ef4444"),
        ConnectionModel(id="w2", from_component="esp32", from_pin="GND_1", to_component="relay_1", to_pin="gnd", color="#0f172a"),
        ConnectionModel(id="w3", from_component="esp32", from_pin="GPIO19", to_component="relay_1", to_pin="in", color="#3b82f6"),
    ])
    return proj


def create_neopixel_example() -> ProjectModel:
    code = """# Exemple 10 : Éclairage RGB adressable NeoPixel WS2812B
from machine import Pin
from time import sleep
import neopixel

# Anneau de 8 LEDs NeoPixel sur GPIO 5
np = neopixel.NeoPixel(Pin(5), 8)
print("Animations lumineuses NeoPixel...")

# Couleurs de base : Rouge, Vert, Bleu, Jaune, Cyan, Magenta, Blanc, Éteint
palette = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (0, 255, 255), (255, 0, 255),
    (255, 255, 255), (0, 0, 0)
]

while True:
    for color in palette:
        np.fill(color)
        np.write()
        sleep(0.5)
"""
    proj = ProjectModel(name="NeoPixel WS2812B", description="Animation de LED RGB adressables", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=260, y=50)
    np_comp = ComponentModel(id="np_1", type="neopixel", x=330, y=140, properties={"num_leds": 8})
    proj.components.extend([breadboard, np_comp])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="esp32", from_pin="5V", to_component="np_1", to_pin="5v", color="#ef4444"),
        ConnectionModel(id="w2", from_component="esp32", from_pin="GND_1", to_component="np_1", to_pin="gnd", color="#0f172a"),
        ConnectionModel(id="w3", from_component="esp32", from_pin="GPIO5", to_component="np_1", to_pin="din", color="#10b981"),
    ])
    return proj


def create_wifi_example() -> ProjectModel:
    code = """# Exemple 11 : Connexion Wi-Fi & Serveur Web IoT MicroPython
import network
from machine import Pin
from time import sleep

# Initialisation du module Wi-Fi Station
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print("Connexion au réseau Wi-Fi virtuel...")
wlan.connect("ESP32_Lab_WiFi", "motdepasse123")

while not wlan.isconnected():
    print("En attente de connexion Wi-Fi...")
    sleep(0.5)

ip_info = wlan.ifconfig()
print(f"Connecté avec succès !")
print(f"Adresse IP ESP32 : {ip_info[0]}")
print(f"Serveur Web actif sur http://{ip_info[0]}/")
"""
    proj = ProjectModel(name="Wi-Fi & Serveur Web IoT", description="Connexion réseau sans fil MicroPython", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=260, y=50)
    proj.components.append(breadboard)
    return proj


def create_ble_example() -> ProjectModel:
    code = """# Exemple 12 : Balise & Communication Bluetooth Low Energy (BLE)
import bluetooth
from time import sleep

print("=== Démarrage du contrôleur Bluetooth BLE ===")

# Initialisation de la radio BLE
ble = bluetooth.BLE()
ble.active(True)
ble.config(gap_name="ESP32_Lab_BLE")

print(f"Nom du périphérique BLE : {ble.config('gap_name')}")

# Enregistrement d'un service GATT de télémétrie
SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
CHAR_TEMP_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")

services = [
    (SERVICE_UUID, [(CHAR_TEMP_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY)]),
]

((char_handle,),) = ble.gatts_register_services(services)
print(f"Service GATT enregistré (Handle: {char_handle})")

# Démarrage de la diffusion publicitaire (Advertising)
# Paquet ADV avec nom 'ESP32_Lab'
adv_data = b"\\x02\\x01\\x06\\x0a\\x09ESP32_Lab"
ble.gap_advertise(100, adv_data)
print("Diffusion publicitaire (Advertising) active et détectable...")

# Simulation d'envoi de mesures de température par notifications BLE
for temp in [22.5, 23.1, 23.8, 24.0]:
    msg = f"Temp: {temp} C".encode()
    ble.gatts_write(char_handle, msg)
    ble.gatts_notify(0, char_handle, msg)
    print(f"Notification BLE émise -> {msg.decode()}")
    sleep(1.0)

print("Test BLE terminé avec succès.")
"""
    proj = ProjectModel(name="Bluetooth Low Energy (BLE)", description="Balise et service GATT Bluetooth MicroPython", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=260, y=50)
    proj.components.append(breadboard)
    return proj


def create_weather_iot_example() -> ProjectModel:
    code = """# Exemple 13 : Station Météo IoT connectée au Cloud (API Web Réelle)
# Cet exemple utilise la véritable connexion Internet de votre PC
# pour interroger l'API météo Open-Meteo en direct !

import network
import urequests
from time import sleep

print("=== Station Météo Cloud IoT MicroPython ===")

# 1. Connexion au réseau
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print("Connexion au réseau Wi-Fi...")
wlan.connect("ESP32_WiFi", "password")

ip, mask, gw, dns = wlan.ifconfig()
print(f"Liaison active ! IP de l'ESP32 : {ip}")

# 2. Interrogation d'une véritable API REST mondiale (Open-Meteo)
print("Récupération de la météo en direct (Paris)...")
url = "https://api.open-meteo.com/v1/forecast?latitude=48.85&longitude=2.35&current=temperature_2m,relative_humidity_2m,wind_speed_10m"

try:
    response = urequests.get(url, timeout=10.0)
    if response.status_code == 200:
        data = response.json()
        current = data.get("current", {})
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")

        print("----------------------------------------")
        print("🌍 RÉSULTATS MÉTÉO RÉELS EN DIRECT :")
        print(f"🌡️  Température extérieure : {temp} °C")
        print(f"💧 Humidité relative      : {humidity} %")
        print(f"💨 Vitesse du vent         : {wind} km/h")
        print("----------------------------------------")
    else:
        print(f"Erreur API (Code HTTP: {response.status_code})")
    response.close()
except Exception as e:
    print(f"Erreur lors de la requête Web : {e}")

print("Simulation IoT terminée avec succès.")
"""
    proj = ProjectModel(name="Station Météo Cloud (API Réelle)", description="Requête HTTP REST en direct via la passerelle Internet du PC", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=260, y=50)
    proj.components.append(breadboard)
    return proj


def create_wifi_scanner_example() -> ProjectModel:
    code = """# ==========================================================
# SCANNER DE RÉSEAUX WI-FI (MicroPython ESP32)
# ==========================================================
# Ce script scanne et affiche la liste des réseaux Wi-Fi
# avec leur nom (SSID), canal, puissance (RSSI) et sécurité.
# ==========================================================

import network
import time

AUTH_MODES = {
    0: "Ouvert (Sans mot de passe)",
    1: "WEP",
    2: "WPA-PSK",
    3: "WPA2-PSK",
    4: "WPA/WPA2-PSK",
    5: "WPA2-Enterprise",
    6: "WPA3-PSK",
}

print("=== SCANNER DE RÉSEAUX SANS-FIL ESP32 ===")
print("Activation de l'interface radio Wi-Fi...")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Scan en cours des points d'accès disponibles...")
print("")
networks = wlan.scan()

print(f"📡 {len(networks)} réseau(x) Wi-Fi détecté(s) :")
print("")
print(f"{'SSID (Nom du réseau)':<26} | {'Canal':<6} | {'Signal (RSSI)':<14} | {'Sécurité'}")
print("-" * 75)

# Tri des réseaux du plus puissant au plus éloigné
for net in sorted(networks, key=lambda x: x[3], reverse=True):
    ssid_bytes, bssid, channel, rssi, authmode, hidden = net
    ssid = ssid_bytes.decode('utf-8', errors='replace') if ssid_bytes else "<Réseau Masqué>"

    # Évaluation de la qualité de réception
    if rssi >= -50:
        bar = "📶 [████] Excellent"
    elif rssi >= -65:
        bar = "📶 [███ ] Bon"
    elif rssi >= -75:
        bar = "📶 [██  ] Moyen"
    else:
        bar = "📶 [█   ] Faible"

    auth_str = AUTH_MODES.get(authmode, f"Mode {authmode}")
    print(f"{ssid:<26} | {channel:<6} | {rssi:>4} dBm        | {auth_str} ({bar})")

print("-" * 75)
print("Scan des réseaux terminé avec succès.")
"""
    proj = ProjectModel(name="Scanner de Réseaux Wi-Fi", description="Découverte et analyse des points d'accès sans-fil environnants", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=260, y=50)
    proj.components.append(breadboard)
    return proj


def create_mqtt_example() -> ProjectModel:
    code = """# ==========================================================
# CLIENT MQTT IOT - TÉLÉMÉTRIE CLOUD (MicroPython ESP32)
# ==========================================================
# Cet exemple se connecte à un broker MQTT public mondial (HiveMQ)
# et échange des messages en temps réel (Publication & Abonnement).
# ==========================================================

import network
import time
from umqtt.simple import MQTTClient

print("=== DÉMARRAGE DU CLIENT MQTT IOT ===")

# 1. Connexion au réseau
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("ESP32_WiFi", "password")

ip, mask, gw, dns = wlan.ifconfig()
print(f"Liaison active ! IP : {ip}")

# 2. Paramètres du Broker MQTT public
BROKER = "broker.hivemq.com"
TOPIC_TELEMETRY = "esp32_lab/telemetry"
TOPIC_CONTROL = "esp32_lab/control"

# Callback appelé lors de la réception d'un message
def on_message_received(topic, msg):
    print("----------------------------------------")
    print(f"📩 MESSAGE REÇU DU CLOUD MQTT :")
    print(f"   Canal   : {topic.decode()}")
    print(f"   Donnée  : {msg.decode()}")
    print("----------------------------------------")

# 3. Connexion au Broker
client_id = f"esp32_lab_{int(time.time())}"
print(f"Connexion au broker MQTT [{BROKER}:1883]...")

try:
    client = MQTTClient(client_id, BROKER, port=1883)
    client.set_callback(on_message_received)
    client.connect()
    print("✅ Connecté au Broker MQTT avec succès !")

    # 4. Abonnement (Subscribe) au canal de contrôle
    client.subscribe(TOPIC_CONTROL)
    print(f"📡 Abonné au topic de commande : {TOPIC_CONTROL}")
    print(f"📡 Télémétrie diffusée sur     : {TOPIC_TELEMETRY}")
    print("--------------------------------------------------")
    print("💡 Vous pouvez publier des ordres depuis HiveMQ Web !")
    print("   (Exemple : Topic='esp32_lab/control' Message='LED ON')")
    print("--------------------------------------------------")

    counter = 1
    temp_sim = 21.5
    while True:
        t = time.localtime()
        time_str = f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        payload = f'{{"device": "ESP32_Lab", "temperature": {temp_sim:.1f}, "count": {counter}, "status": "online"}}'
        client.publish(TOPIC_TELEMETRY, payload)
        print(f"📤 [{time_str}] Télémétrie publiée -> {payload}")
        
        # Écoute continue des messages du cloud pendant l'intervalle
        for _ in range(40):
            client.check_msg()
            time.sleep(0.1)
            
        counter += 1
        temp_sim += 0.3
        if temp_sim > 28.0:
            temp_sim = 21.0

except Exception as e:
    print(f"Erreur MQTT : {e}")
finally:
    try:
        client.disconnect()
        print("🔌 Déconnexion propre du broker MQTT effectuée.")
    except Exception:
        pass

print("Session MQTT terminée.")
"""
    proj = ProjectModel(name="Client MQTT IoT (Cloud)", description="Publication et souscription MQTT en temps réel via broker public", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=260, y=50)
    proj.components.append(breadboard)
    return proj


def create_ble_scanner_example() -> ProjectModel:
    code = """# ==========================================================
# EXPLORATEUR DE PÉRIPHÉRIQUES BLUETOOTH BLE (MicroPython)
# ==========================================================
# Ce script active le contrôleur BLE de l'ESP32 et effectue
# un scan de découverte des appareils et balises Bluetooth à proximité.
# ==========================================================

import bluetooth
import time
from micropython import const

_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

print("=== SCANNER DE PÉRIPHÉRIQUES BLUETOOTH BLE ===")

# Liste pour collecter les appareils détectés
devices_found = []

def decode_name(adv_data):
    \"\"\"Extrait le nom complet du périphérique dans la trame publicitaire BLE.\"\"\"
    i = 0
    while i < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        type_ = adv_data[i + 1]
        # 0x08 = Shortened Local Name, 0x09 = Complete Local Name
        if type_ in (0x08, 0x09):
            try:
                return adv_data[i + 2 : i + 1 + length].decode("utf-8")
            except Exception:
                return "Inconnu"
        i += 1 + length
    return "Appareil BLE anonyme"

def format_mac(addr_bytes):
    \"\"\"Convertit les 6 octets d'adresse en format MAC standard.\"\"\"
    return ":".join(f"{b:02X}" for b in addr_bytes)

def bt_irq(event, data):
    if event == _IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data
        name = decode_name(adv_data)
        mac = format_mac(addr)
        devices_found.append((name, mac, rssi))
    elif event == _IRQ_SCAN_DONE:
        print("✅ Scan BLE terminé.")

# 1. Initialisation de la radio BLE
ble = bluetooth.BLE()
print("Activation du contrôleur Bluetooth BLE...")
ble.active(True)
ble.irq(bt_irq)

# 2. Lancement du scan
print("Recherche active des balises et périphériques Bluetooth...")
ble.gap_scan(duration_ms=2000, interval_us=30000, window_us=30000)

time.sleep(2.2)

# 3. Affichage des résultats
print(f"\\n📱 {len(devices_found)} périphérique(s) Bluetooth détecté(s) :\\n")
print(f"{'Nom du Périphérique':<28} | {'Adresse MAC':<17} | {'Signal (RSSI)':<12}")
print("-" * 65)

for name, mac, rssi in sorted(devices_found, key=lambda x: x[2], reverse=True):
    bar_count = max(1, min(4, int((rssi + 100) / 12)))
    bars = "[" + "█" * bar_count + " " * (4 - bar_count) + "]"
    print(f"{name:<28} | {mac:<17} | {rssi:>4} dBm {bars}")

print("-" * 65)
ble.active(False)
print("Radio BLE désactivée pour économie d'énergie.")
print("Exploration terminée avec succès.")
"""
    proj = ProjectModel(name="Scanner Bluetooth BLE", description="Découverte et analyse des balises et périphériques Bluetooth BLE environnants", files={"main.py": code})
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=260, y=50)
    proj.components.append(breadboard)
    return proj

