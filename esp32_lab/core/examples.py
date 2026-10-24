"""
Bibliothèque de projets et d'exemples pré-câblés pour ESP32 MicroPython Lab
"""

from .models.component import ComponentModel, ComponentPin
from .models.connection import ConnectionModel
from .models.project import ProjectModel


def get_esp32_examples() -> dict[str, ProjectModel]:
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


def get_uno_examples() -> dict[str, ProjectModel]:
    return {
        "uno_blink": create_uno_blink_example(),
        "uno_button_led": create_uno_button_led_example(),
        "uno_pot_pwm": create_uno_pot_pwm_example(),
        "uno_servo": create_uno_servo_example(),
        "uno_traffic_lights": create_uno_traffic_lights_example(),
        "uno_lcd": create_uno_lcd_example(),
    }


def get_all_examples() -> dict[str, ProjectModel]:
    examples = get_esp32_examples()
    examples.update(get_uno_examples())
    return examples


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


# =============================================================================
# EXEMPLES OFFICIELS C++ ARDUINO (ARDUINO UNO R3)
# =============================================================================

def create_uno_blink_example() -> ProjectModel:
    code = """// Exemple 1 : Clignotement de LED sur Arduino Uno
const int LED_PIN = 13; // Broche numérique 13 (LED intégrée 'L')

void setup() {
  // Configuration de la broche en sortie numérique
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  Serial.println("Arduino Uno démarré : clignotement D13...");
}

void loop() {
  // Allumer la LED (niveau logique HAUT / 5V)
  digitalWrite(LED_PIN, HIGH);
  Serial.println("LED ALLUMÉE (HIGH)");
  delay(1000); // Pause de 1000 millisecondes

  // Éteindre la LED (niveau logique BAS / 0V)
  digitalWrite(LED_PIN, LOW);
  Serial.println("LED ÉTEINTE (LOW)");
  delay(1000); // Pause de 1000 millisecondes
}
"""
    proj = ProjectModel(
        name="LED Clignotante (Arduino Uno)",
        description="Clignotement périodique d'une LED rouge connectée sur la broche numérique D13 et LED intégrée 'L'",
        board_id="arduino_uno",
        language="arduino_c",
        files={"sketch.ino": code}
    )
    uno = ComponentModel(id="arduino_uno", type="arduino_uno", name="Arduino Uno R3", x=60, y=60)
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=300, y=50)
    led = ComponentModel(id="led_1", type="led", name="LED Rouge", x=354.5, y=129.0, properties={"color": "red"}, pin_insertions={"anode": "r10_b", "cathode": "r11_b"})
    res = ComponentModel(id="res_1", type="resistor", name="Résistance 220Ω", x=363.0, y=188.5, properties={"value": 220}, pin_insertions={"pin1": "r11_c", "pin2": "r17_c"})
    proj.components.extend([uno, breadboard, led, res])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="arduino_uno", from_pin="13", to_component="breadboard_1", to_pin="r10_a", color="#ef4444"),
        ConnectionModel(id="w2", from_component="breadboard_1", from_pin="r17_a", to_component="breadboard_1", to_pin="rail_l_minus_17", color="#1e293b"),
        ConnectionModel(id="w3", from_component="breadboard_1", from_pin="rail_l_minus_28", to_component="arduino_uno", to_pin="GND_1", color="#0f172a"),
    ])
    return proj


def create_uno_button_led_example() -> ProjectModel:
    code = """// Exemple 2 : Bouton Poussoir et LED (Arduino Uno)
const int BUTTON_PIN = 2; // Broche bouton poussoir
const int LED_PIN = 13;    // Broche LED

void setup() {
  // Activation de la résistance interne de tirage vers le haut
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  Serial.println("Contrôle interactif : appuyez sur le bouton D2...");
}

void loop() {
  int etat = digitalRead(BUTTON_PIN);
  
  // Avec INPUT_PULLUP : le bouton pressé tire la broche à LOW (0V)
  if (etat == LOW) {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Bouton pressé -> LED ALLUMÉE");
  } else {
    digitalWrite(LED_PIN, LOW);
  }
  delay(50);
}
"""
    proj = ProjectModel(
        name="Bouton Poussoir & LED (Arduino Uno)",
        description="Lecture d'une entrée numérique avec pull-up interne et commande immédiate de LED",
        board_id="arduino_uno",
        language="arduino_c",
        files={"sketch.ino": code}
    )
    uno = ComponentModel(id="arduino_uno", type="arduino_uno", name="Arduino Uno R3", x=60, y=60)
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=300, y=50)
    led = ComponentModel(id="led_1", type="led", name="LED Verte", x=354.5, y=112.0, properties={"color": "green"}, pin_insertions={"anode": "r8_b", "cathode": "r9_b"})
    btn = ComponentModel(id="btn_1", type="button", name="Bouton Poussoir", x=399.0, y=214.0, pin_insertions={"pin1": "r16_e", "pin2": "r16_f", "pin3": "r18_e", "pin4": "r18_f"})
    proj.components.extend([uno, breadboard, led, btn])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="arduino_uno", from_pin="13", to_component="breadboard_1", to_pin="r8_a", color="#22c55e"),
        ConnectionModel(id="w2", from_component="breadboard_1", from_pin="r9_a", to_component="breadboard_1", to_pin="rail_l_minus_9", color="#0f172a"),
        ConnectionModel(id="w3", from_component="arduino_uno", from_pin="2", to_component="breadboard_1", to_pin="r16_a", color="#38bdf8"),
        ConnectionModel(id="w4", from_component="breadboard_1", from_pin="r18_a", to_component="breadboard_1", to_pin="rail_l_minus_18", color="#1e293b"),
        ConnectionModel(id="w5", from_component="breadboard_1", from_pin="rail_l_minus_28", to_component="arduino_uno", to_pin="GND_1", color="#0f172a"),
    ])
    return proj


def create_uno_pot_pwm_example() -> ProjectModel:
    code = """// Exemple 3 : Variateur PWM et Potentiomètre (Arduino Uno)
const int POT_PIN = A0; // Entrée analogique A0
const int LED_PIN = 9;  // Sortie PWM ~9

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  Serial.println("Variateur PWM démarré : tournez le potentiomètre (A0)");
}

void loop() {
  // Lecture de la tension sur 10 bits (0 à 1023)
  int val_adc = analogRead(POT_PIN);
  
  // Étalonnage de la valeur 0-1023 vers le rapport cyclique PWM 0-255
  int pwm = map(val_adc, 0, 1023, 0, 255);
  analogWrite(LED_PIN, pwm);

  Serial.print("Tension ADC A0 : ");
  Serial.print(val_adc);
  Serial.print(" | Rapport PWM D9 : ");
  Serial.println(pwm);
  delay(100);
}
"""
    proj = ProjectModel(
        name="Variateur PWM & Potentiomètre (Arduino Uno)",
        description="Conversion analogique-numérique (ADC A0) et gradation de LED en modulation de largeur d'impulsion (PWM D9)",
        board_id="arduino_uno",
        language="arduino_c",
        files={"sketch.ino": code}
    )
    uno = ComponentModel(id="arduino_uno", type="arduino_uno", name="Arduino Uno R3", x=60, y=60)
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=300, y=50)
    pot = ComponentModel(id="pot_1", type="potentiometer", name="Potentiomètre 10kΩ", x=380.0, y=140.0, properties={"raw_value": 512}, pin_insertions={"vcc": "r10_d", "sig": "r11_d", "gnd": "r12_d"})
    led = ComponentModel(id="led_1", type="led", name="LED Bleue", x=354.5, y=230.0, properties={"color": "blue"}, pin_insertions={"anode": "r20_b", "cathode": "r21_b"})
    res = ComponentModel(id="res_1", type="resistor", name="Résistance 220Ω", x=363.0, y=280.0, properties={"value": 220}, pin_insertions={"pin1": "r21_c", "pin2": "r26_c"})
    proj.components.extend([uno, breadboard, pot, led, res])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="arduino_uno", from_pin="5V", to_component="breadboard_1", to_pin="r10_a", color="#ef4444"),
        ConnectionModel(id="w2", from_component="breadboard_1", from_pin="r11_a", to_component="arduino_uno", to_pin="A0", color="#38bdf8"),
        ConnectionModel(id="w3", from_component="breadboard_1", from_pin="r12_a", to_component="breadboard_1", to_pin="rail_l_minus_12", color="#1e293b"),
        ConnectionModel(id="w4", from_component="arduino_uno", from_pin="9", to_component="breadboard_1", to_pin="r20_a", color="#3b82f6"),
        ConnectionModel(id="w5", from_component="breadboard_1", from_pin="r26_a", to_component="breadboard_1", to_pin="rail_l_minus_26", color="#1e293b"),
        ConnectionModel(id="w6", from_component="breadboard_1", from_pin="rail_l_minus_28", to_component="arduino_uno", to_pin="GND_1", color="#0f172a"),
    ])
    return proj


def create_uno_servo_example() -> ProjectModel:
    code = """// Exemple 4 : Balayage Servomoteur (Arduino Uno)
#include <Servo.h>

Servo monServo;
const int SERVO_PIN = 9;

void setup() {
  monServo.attach(SERVO_PIN);
  Serial.begin(9600);
  Serial.println("Initialisation du servomoteur sur broche D9...");
}

void loop() {
  // Rotation progressive de 0 à 180 degrés
  for (int pos = 0; pos <= 180; pos += 15) {
    monServo.write(pos);
    Serial.print("Position servomoteur : ");
    Serial.println(pos);
    delay(100);
  }
  delay(400);

  // Retour progressif de 180 à 0 degrés
  for (int pos = 180; pos >= 0; pos -= 15) {
    monServo.write(pos);
    Serial.print("Position servomoteur : ");
    Serial.println(pos);
    delay(100);
  }
  delay(400);
}
"""
    proj = ProjectModel(
        name="Balayage Servomoteur SG90 (Arduino Uno)",
        description="Pilotage angulaire précis d'un servomoteur avec la bibliothèque standard Servo.h",
        board_id="arduino_uno",
        language="arduino_c",
        files={"sketch.ino": code}
    )
    uno = ComponentModel(id="arduino_uno", type="arduino_uno", name="Arduino Uno R3", x=60, y=60)
    servo = ComponentModel(id="servo_1", type="servo", name="Servomoteur SG90", x=380, y=120, properties={"angle": 90.0})
    proj.components.extend([uno, servo])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="arduino_uno", from_pin="9", to_component="servo_1", to_pin="sig", color="#f97316"),
        ConnectionModel(id="w2", from_component="arduino_uno", from_pin="5V", to_component="servo_1", to_pin="vcc", color="#ef4444"),
        ConnectionModel(id="w3", from_component="arduino_uno", from_pin="GND_1", to_component="servo_1", to_pin="gnd", color="#0f172a"),
    ])
    return proj


def create_uno_traffic_lights_example() -> ProjectModel:
    code = """// Exemple 5 : Carrefour à Feux Tricolores (Arduino Uno)
const int FEU_ROUGE = 12;
const int FEU_JAUNE = 11;
const int FEU_VERT  = 10;

void setup() {
  pinMode(FEU_ROUGE, OUTPUT);
  pinMode(FEU_JAUNE, OUTPUT);
  pinMode(FEU_VERT,  OUTPUT);
  Serial.begin(9600);
  Serial.println("Contrôleur de carrefour routier démarré.");
}

void loop() {
  // 1. Feu Vert
  Serial.println("🟢 Feu Vert : Passage autorisé");
  digitalWrite(FEU_VERT, HIGH);
  digitalWrite(FEU_JAUNE, LOW);
  digitalWrite(FEU_ROUGE, LOW);
  delay(3000);

  // 2. Feu Jaune
  Serial.println("🟡 Feu Jaune : Ralentissement");
  digitalWrite(FEU_VERT, LOW);
  digitalWrite(FEU_JAUNE, HIGH);
  delay(1000);

  // 3. Feu Rouge
  Serial.println("🔴 Feu Rouge : Arrêt obligatoire");
  digitalWrite(FEU_JAUNE, LOW);
  digitalWrite(FEU_ROUGE, HIGH);
  delay(3000);
}
"""
    proj = ProjectModel(
        name="Feux Tricolores (Arduino Uno)",
        description="Séquenceur temporel pour gestion de carrefour routier avec 3 sorties numériques",
        board_id="arduino_uno",
        language="arduino_c",
        files={"sketch.ino": code}
    )
    uno = ComponentModel(id="arduino_uno", type="arduino_uno", name="Arduino Uno R3", x=60, y=60)
    breadboard = ComponentModel(id="breadboard_1", type="breadboard", x=300, y=50)
    led_v = ComponentModel(id="led_vert", type="led", name="Feu Vert", x=354.5, y=100.0, properties={"color": "green"}, pin_insertions={"anode": "r6_b", "cathode": "r7_b"})
    res_v = ComponentModel(id="res_v", type="resistor", name="Résistance 220Ω", x=363.0, y=130.0, properties={"value": 220}, pin_insertions={"pin1": "r7_c", "pin2": "r10_c"})
    led_j = ComponentModel(id="led_jaune", type="led", name="Feu Jaune", x=354.5, y=160.0, properties={"color": "yellow"}, pin_insertions={"anode": "r12_b", "cathode": "r13_b"})
    res_j = ComponentModel(id="res_j", type="resistor", name="Résistance 220Ω", x=363.0, y=190.0, properties={"value": 220}, pin_insertions={"pin1": "r13_c", "pin2": "r16_c"})
    led_r = ComponentModel(id="led_rouge", type="led", name="Feu Rouge", x=354.5, y=220.0, properties={"color": "red"}, pin_insertions={"anode": "r18_b", "cathode": "r19_b"})
    res_r = ComponentModel(id="res_r", type="resistor", name="Résistance 220Ω", x=363.0, y=250.0, properties={"value": 220}, pin_insertions={"pin1": "r19_c", "pin2": "r22_c"})
    proj.components.extend([uno, breadboard, led_v, res_v, led_j, res_j, led_r, res_r])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="arduino_uno", from_pin="10", to_component="breadboard_1", to_pin="r6_a", color="#22c55e"),
        ConnectionModel(id="w2", from_component="arduino_uno", from_pin="11", to_component="breadboard_1", to_pin="r12_a", color="#eab308"),
        ConnectionModel(id="w3", from_component="arduino_uno", from_pin="12", to_component="breadboard_1", to_pin="r18_a", color="#ef4444"),
        ConnectionModel(id="w4", from_component="breadboard_1", from_pin="r10_a", to_component="breadboard_1", to_pin="rail_l_minus_10", color="#1e293b"),
        ConnectionModel(id="w5", from_component="breadboard_1", from_pin="r16_a", to_component="breadboard_1", to_pin="rail_l_minus_16", color="#1e293b"),
        ConnectionModel(id="w6", from_component="breadboard_1", from_pin="r22_a", to_component="breadboard_1", to_pin="rail_l_minus_22", color="#1e293b"),
        ConnectionModel(id="w7", from_component="breadboard_1", from_pin="rail_l_minus_28", to_component="arduino_uno", to_pin="GND_1", color="#0f172a"),
    ])
    return proj


def create_uno_lcd_example() -> ProjectModel:
    code = """// Exemple 6 : Afficheur LCD 16x2 (Arduino Uno)
#include <LiquidCrystal.h>

// Initialisation de la bibliothèque avec les broches d'interface
// LiquidCrystal(rs, enable, d4, d5, d6, d7)
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  // Configuration du nombre de colonnes et de lignes du LCD (16x2)
  lcd.begin(16, 2);
  lcd.print("Arduino Uno Lab");
  lcd.setCursor(0, 1);
  lcd.print("Simulateur v4.0");
  delay(2000);
  lcd.clear();
  lcd.print("Temps : ");
}

void loop() {
  // Déplacer le curseur à la colonne 8, ligne 0
  lcd.setCursor(8, 0);
  lcd.print(millis() / 1000);
  lcd.print(" s");
  delay(500);
}
"""
    proj = ProjectModel(
        name="Afficheur LCD 1602 (Arduino Uno)",
        description="Affichage alphanumérique dynamique avec la bibliothèque officielle LiquidCrystal.h",
        board_id="arduino_uno",
        language="arduino_c",
        files={"sketch.ino": code}
    )
    uno = ComponentModel(id="arduino_uno", type="arduino_uno", name="Arduino Uno R3", x=60, y=60)
    lcd = ComponentModel(id="lcd_1", type="lcd", name="Écran LCD 16x2", x=360, y=100)
    proj.components.extend([uno, lcd])
    proj.connections.extend([
        ConnectionModel(id="w1", from_component="arduino_uno", from_pin="12", to_component="lcd_1", to_pin="rs", color="#3b82f6"),
        ConnectionModel(id="w2", from_component="arduino_uno", from_pin="11", to_component="lcd_1", to_pin="en", color="#38bdf8"),
        ConnectionModel(id="w3", from_component="arduino_uno", from_pin="5", to_component="lcd_1", to_pin="d4", color="#10b981"),
        ConnectionModel(id="w4", from_component="arduino_uno", from_pin="4", to_component="lcd_1", to_pin="d5", color="#eab308"),
        ConnectionModel(id="w5", from_component="arduino_uno", from_pin="3", to_component="lcd_1", to_pin="d6", color="#f97316"),
        ConnectionModel(id="w6", from_component="arduino_uno", from_pin="2", to_component="lcd_1", to_pin="d7", color="#ef4444"),
        ConnectionModel(id="w7", from_component="arduino_uno", from_pin="5V", to_component="lcd_1", to_pin="vcc", color="#dc2626"),
        ConnectionModel(id="w8", from_component="arduino_uno", from_pin="GND_1", to_component="lcd_1", to_pin="gnd", color="#0f172a"),
    ])
    return proj

