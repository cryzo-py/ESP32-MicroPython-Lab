"""
Catalogue des cours et leçons interactives pour ESP32 MicroPython Lab
"""

from dataclasses import dataclass, field
from .models.project import ProjectModel
from .examples import (
    create_blink_example,
    create_button_led_example,
    create_pot_pwm_example,
    create_servo_example,
    create_dht22_example,
    create_oled_example,
    create_hcsr04_example,
    create_lcd_example,
    create_relay_example,
    create_neopixel_example,
    create_wifi_example,
    create_uno_blink_example,
    create_uno_button_led_example,
    create_uno_pot_pwm_example,
    create_uno_servo_example,
    create_uno_traffic_lights_example,
    create_uno_lcd_example,
)


@dataclass
class Lesson:
    id: str
    chapter_num: int
    chapter_title: str
    title: str
    summary: str
    theory: str
    challenge: str
    required_components: list[str]
    target_pin: int | None = None
    starter_project: ProjectModel | None = None
    board_id: str = "esp32_wroom_32"
    language: str = "micropython"


def get_esp32_curriculum() -> list[Lesson]:
    return [
        Lesson(
            id="lesson_1_gpio_led",
            chapter_num=1,
            chapter_title="Chapitre 1 : Sorties Numériques & GPIO",
            title="TP 1 : Ma première LED clignotante",
            summary="Apprenez à configurer une broche en sortie et à générer des impulsions temporelles.",
            theory=(
                "### Qu'est-ce qu'une broche GPIO ?\n\n"
                "Le microcontrôleur ESP32 possède des broches **GPIO** (General Purpose Input/Output).\n"
                "En MicroPython, on utilise le module `machine` et la classe `Pin` :\n\n"
                "```python\n"
                "from machine import Pin\n"
                "from time import sleep\n\n"
                "# Configuration du GPIO 2 en sortie\n"
                "led = Pin(2, Pin.OUT)\n"
                "led.value(1) # Allume la LED (3.3V)\n"
                "sleep(1)     # Attend 1 seconde\n"
                "led.value(0) # Éteint la LED (0V)\n"
                "```\n\n"
                "Une LED nécessite toujours une résistance de limitation (typiquement 220 Ω ou 330 Ω) pour ne pas griller."
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Placez une **LED** et une **Résistance** sur la platine d'essai.\n"
                "2. Reliez l'anode au **GPIO 2** et la cathode au **GND** via la résistance.\n"
                "3. Écrivez un programme qui fait clignoter la LED avec une période de 1 seconde (1s ON, 1s OFF).\n"
                "4. Cliquez sur **« ✅ Évaluer mon travail »** pour valider votre note."
            ),
            required_components=["led", "resistor"],
            target_pin=2,
            starter_project=create_blink_example()
        ),
        Lesson(
            id="lesson_2_button",
            chapter_num=2,
            chapter_title="Chapitre 2 : Entrées Numériques & Boutons",
            title="TP 2 : Contrôle interactif par bouton poussoir",
            summary="Découvrez comment lire l'état d'un bouton poussoir et gérer les résistances de tirage.",
            theory=(
                "### Les entrées numériques et le Pull-down / Pull-up\n\n"
                "Pour lire l'état d'un bouton, on configure la broche avec `Pin.IN` :\n\n"
                "```python\n"
                "from machine import Pin\n\n"
                "bouton = Pin(4, Pin.IN, Pin.PULL_DOWN)\n"
                "etat = bouton.value() # Vaut 1 si pressé, 0 si relâché\n"
                "```\n\n"
                "La résistance de tirage (*pull-down*) garantit un niveau logique 0 stable quand le bouton n'est pas actionné."
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez un **bouton poussoir** sur le **GPIO 4**.\n"
                "2. Connectez une **LED** sur le **GPIO 2**.\n"
                "3. Écrivez un script qui allume la LED tant que le bouton virtuel est maintenu pressé."
            ),
            required_components=["button", "led"],
            target_pin=4,
            starter_project=create_button_led_example()
        ),
        Lesson(
            id="lesson_3_pot_adc",
            chapter_num=3,
            chapter_title="Chapitre 3 : Entrées Analogiques (ADC)",
            title="TP 3 : Lecture de tension avec Potentiomètre",
            summary="Convertissez une tension analogique variable (0-3.3V) en valeur numérique 12 bits.",
            theory=(
                "### Convertisseur Analogique-Numérique (ADC)\n\n"
                "L'ESP32 intègre des convertisseurs ADC 12 bits qui transforment une tension de 0 à 3.3V en une valeur de 0 à 4095 :\n\n"
                "```python\n"
                "from machine import Pin, ADC\n\n"
                "adc = ADC(Pin(34))\n"
                "valeur = adc.read() # Renvoie 0 à 4095\n"
                "tension = valeur * 3.3 / 4095\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez la broche SIG du potentiomètre sur le **GPIO 34** (entrée analogique pure).\n"
                "2. Lisez la valeur toutes les 200 ms et affichez-la sur la console avec `print()`."
            ),
            required_components=["potentiometer"],
            target_pin=34,
            starter_project=create_pot_pwm_example()
        ),
        Lesson(
            id="lesson_4_servo_pwm",
            chapter_num=4,
            chapter_title="Chapitre 4 : Modulation de Largeur d'Impulsion (PWM)",
            title="TP 4 : Pilotage angulaire d'un Servomoteur SG90",
            summary="Générez un signal PWM 50 Hz pour positionner un servomoteur de 0° à 180°.",
            theory=(
                "### Pilotage par PWM\n\n"
                "Un servomoteur standard SG90 attend un train d'impulsions à 50 Hz (période de 20 ms) :\n"
                "- Impulsion de 0.5 ms -> 0°\n"
                "- Impulsion de 1.5 ms -> 90° (centre)\n"
                "- Impulsion de 2.5 ms -> 180°\n\n"
                "```python\n"
                "from machine import Pin, PWM\n\n"
                "servo = PWM(Pin(18), freq=50)\n"
                "# Rapport cyclique adapté pour 90°\n"
                "servo.duty(77)\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Reliez le servomoteur au **GPIO 18**.\n"
                "2. Programmez un balayage automatique d'angle de 0° à 180° puis retour à 0°."
            ),
            required_components=["servo"],
            target_pin=18,
            starter_project=create_servo_example()
        ),
        Lesson(
            id="lesson_5_dht22",
            chapter_num=5,
            chapter_title="Chapitre 5 : Capteurs Environnementaux",
            title="TP 5 : Station Météo avec Capteur DHT22",
            summary="Mesurez la température et le taux d'humidité ambiante via le protocole numérique DHT.",
            theory=(
                "### Le capteur numérique DHT22\n\n"
                "Le capteur DHT22 utilise un protocole sur un seul fil de données :\n\n"
                "```python\n"
                "import dht\n"
                "from machine import Pin\n\n"
                "capteur = dht.DHT22(Pin(4))\n"
                "capteur.measure()\n"
                "temperature = capteur.temperature() # °C\n"
                "humidite = capteur.humidity()       # %\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez la broche DATA du DHT22 sur le **GPIO 4**.\n"
                "2. Récupérez les mesures et affichez-les dans la console toutes les 2 secondes."
            ),
            required_components=["dht22"],
            target_pin=4,
            starter_project=create_dht22_example()
        ),
        Lesson(
            id="lesson_6_oled",
            chapter_num=6,
            chapter_title="Chapitre 6 : Afficheurs Graphiques I2C",
            title="TP 6 : Affichage sur écran OLED SSD1306",
            summary="Pilotez un écran graphique 128x64 pixels sur le bus série I2C.",
            theory=(
                "### Le bus I2C et l'écran SSD1306\n\n"
                "Le bus I2C utilise deux broches : **SDA** (données, GPIO 21) et **SCL** (horloge, GPIO 22).\n\n"
                "```python\n"
                "from machine import Pin, I2C\n"
                "import ssd1306\n\n"
                "i2c = I2C(scl=Pin(22), sda=Pin(21))\n"
                "oled = ssd1306.SSD1306_I2C(128, 64, i2c)\n"
                "oled.fill(0)\n"
                "oled.text('ESP32 LAB', 20, 10, 1)\n"
                "oled.show()\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Raccordez l'écran OLED sur les broches I2C de l'ESP32 (SCL sur GPIO 22, SDA sur GPIO 21).\n"
                "2. Tracez un cadre avec `rect()` et affichez un message de bienvenue centré."
            ),
            required_components=["oled"],
            target_pin=21,
            starter_project=create_oled_example()
        ),
        Lesson(
            id="lesson_7_hcsr04",
            chapter_num=7,
            chapter_title="Chapitre 7 : Capteurs Ultrasons",
            title="TP 7 : Mesure de distance par ultrasons",
            summary="Mesurez des distances sans contact avec le capteur HC-SR04 et MicroPython.",
            theory=(
                "### Principe de l'écho ultrason\n\n"
                "Le capteur HC-SR04 émet une salve ultrasonique via la broche `TRIG` et mesure le temps mis par l'onde pour revenir sur la broche `ECHO`.\n\n"
                "```python\n"
                "from hcsr04 import HCSR04\n\n"
                "# TRIG sur GPIO 5, ECHO sur GPIO 18\n"
                "sonar = HCSR04(trigger_pin=5, echo_pin=18)\n"
                "distance = sonar.distance_cm()\n"
                "print(f'Distance : {distance} cm')\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez `TRIG` au GPIO 5 et `ECHO` au GPIO 18.\n"
                "2. Alimentez le capteur en 5V et GND.\n"
                "3. Affichez la distance mesurée toutes les 500 ms dans la console."
            ),
            required_components=["hcsr04"],
            target_pin=5,
            starter_project=create_hcsr04_example()
        ),
        Lesson(
            id="lesson_8_lcd",
            chapter_num=8,
            chapter_title="Chapitre 8 : Afficheurs Alphanumériques",
            title="TP 8 : Écran LCD 16x2 I2C",
            summary="Connectez et programmez un afficheur LCD à deux lignes de 16 caractères.",
            theory=(
                "### Afficheur LCD 16x2 avec adaptateur PCF8574\n\n"
                "Grâce au bus I2C, seules deux broches de communication sont nécessaires (`SCL` et `SDA`) :\n\n"
                "```python\n"
                "from machine import Pin, I2C\n"
                "from liquidcrystal_i2c import I2cLcd\n\n"
                "i2c = I2C(scl=Pin(22), sda=Pin(21))\n"
                "lcd = I2cLcd(i2c, 0x27, 2, 16)\n"
                "lcd.putstr('Hello ESP32 !')\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez `SDA` au GPIO 21 et `SCL` au GPIO 22.\n"
                "2. Affichez un texte sur la ligne 1 et un compteur de secondes sur la ligne 2."
            ),
            required_components=["lcd"],
            target_pin=21,
            starter_project=create_lcd_example()
        ),
        Lesson(
            id="lesson_9_relay",
            chapter_num=9,
            chapter_title="Chapitre 9 : Commutation de Puissance",
            title="TP 9 : Module Relais Électromécanique 5V",
            summary="Contrôlez des circuits de puissance (lampes, moteurs) en toute isolation grâce à un relais Songle 5V.",
            theory=(
                "### Qu'est-ce qu'un relais électromécanique ?\n\n"
                "Un microcontrôleur ESP32 délivre au maximum 3.3V et quelques dizaines de milliampères sur ses broches GPIO.\n"
                "Pour piloter des charges de forte puissance (ex. 230V AC ou moteurs 12V), on utilise un **relais** commandé par un transistor ou optocoupleur.\n\n"
                "Le module relais comporte :\n"
                "- **VCC** : Alimentation 5V de la bobine\n"
                "- **GND** : Masse commune\n"
                "- **IN** : Signal de commande numérique (GPIO de l'ESP32)\n"
                "- **COM** : Borne commune de commutation\n"
                "- **NO (Normally Open)** : Contact ouvert au repos, fermé quand IN = 1\n"
                "- **NC (Normally Closed)** : Contact fermé au repos, ouvert quand IN = 1\n\n"
                "```python\n"
                "from machine import Pin\n"
                "from time import sleep\n\n"
                "relais = Pin(19, Pin.OUT)\n"
                "relais.value(1) # Ferme le contact NO\n"
                "sleep(2)\n"
                "relais.value(0) # Ouvre le contact NO\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez le module Relais : **VCC** au 5V, **GND** à la masse, et **IN** au **GPIO 19**.\n"
                "2. Écrivez un programme qui active le relais pendant 2 secondes puis le désactive pendant 2 secondes en boucle continue.\n"
                "3. Observez le voyant vert d'état et le basculement physique des contacts du relais."
            ),
            required_components=["relay"],
            target_pin=19,
            starter_project=create_relay_example()
        ),
        Lesson(
            id="lesson_10_neopixel",
            chapter_num=10,
            chapter_title="Chapitre 10 : Éclairage Adressable RGB",
            title="TP 10 : Anneau de LEDs NeoPixel WS2812B",
            summary="Contrôlez individuellement plusieurs LEDs RGB couleur 24 bits à l'aide d'un seul fil de données GPIO.",
            theory=(
                "### Les LEDs intelligentes WS2812B (NeoPixel)\n\n"
                "Chaque puce WS2812B intègre un contrôleur et 3 LEDs (Rouge, Verte, Bleue) avec 256 niveaux par canal (soit 16,7 millions de couleurs).\n"
                "Elles sont connectées en guirlande : le signal sortant de `DOUT` de la première entre dans le `DIN` de la suivante.\n\n"
                "En MicroPython, le module officiel `neopixel` gère le protocole à haute vitesse (800 kHz) :\n\n"
                "```python\n"
                "from machine import Pin\n"
                "import neopixel\n\n"
                "# Anneau de 8 LEDs sur GPIO 5\n"
                "np = neopixel.NeoPixel(Pin(5), 8)\n\n"
                "# Couleur (R, G, B) de 0 à 255\n"
                "np[0] = (255, 0, 0)   # Première LED en Rouge pur\n"
                "np[1] = (0, 255, 0)   # Deuxième LED en Vert pur\n"
                "np.fill((0, 0, 128))  # Toutes les LEDs en Bleu tamisé\n"
                "np.write()            # Envoie le buffer aux LEDs\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez l'anneau NeoPixel : **5V** au 5V, **GND** au GND, et **DIN** au **GPIO 5**.\n"
                "2. Utilisez la classe `NeoPixel` pour faire défiler une séquence de couleurs sur l'ensemble de l'anneau.\n"
                "3. N'oubliez pas d'appeler `np.write()` après chaque modification du buffer pour actualiser l'éclairage."
            ),
            required_components=["neopixel"],
            target_pin=5,
            starter_project=create_neopixel_example()
        ),
        Lesson(
            id="lesson_11_wifi",
            chapter_num=11,
            chapter_title="Chapitre 11 : Connectivité Réseau & IoT",
            title="TP 11 : Wi-Fi & Serveur Web Embarqué",
            summary="Connectez l'ESP32 à un réseau sans fil et hébergez un serveur Web pour piloter des objets connectés.",
            theory=(
                "### Connectivité Wi-Fi sous MicroPython\n\n"
                "L'ESP32 possède un transceiver Wi-Fi 802.11 b/g/n 2.4 GHz intégré.\n"
                "Le module standard `network` permet de configurer l'interface Wi-Fi en mode Station (`STA_IF`, client Wi-Fi) ou Point d'accès (`AP_IF`) :\n\n"
                "```python\n"
                "import network\n"
                "from time import sleep\n\n"
                "wlan = network.WLAN(network.STA_IF)\n"
                "wlan.active(True)\n"
                "wlan.connect('Mon_SSID', 'Mon_MotDePasse')\n\n"
                "while not wlan.isconnected():\n"
                "    sleep(0.5)\n\n"
                "config = wlan.ifconfig()\n"
                "print(f'Connecté ! Adresse IP : {config[0]}')\n"
                "```\n\n"
                "L'ESP32 peut ensuite servir des pages HTML et des APIs REST via des sockets réseau standards."
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Importez le module `network`.\n"
                "2. Activez l'interface `STA_IF` et connectez l'ESP32 au réseau Wi-Fi virtuel avec `wlan.connect(...)`.\n"
                "3. Attendez la confirmation de connexion avec `wlan.isconnected()` et affichez l'adresse IP attribuée avec `wlan.ifconfig()`."
            ),
            required_components=[],
            target_pin=None,
            starter_project=create_wifi_example(),
            board_id="esp32_wroom_32",
            language="micropython",
        ),
    ]


def get_uno_curriculum() -> list[Lesson]:
    return [
        Lesson(
            id="uno_lesson_1_blink",
            chapter_num=1,
            chapter_title="Chapitre 1 : Sorties Numériques & GPIO (C++ Arduino)",
            title="TP 1 (Uno) : Sorties Numériques & LED Clignotante",
            summary="Maîtrisez la configuration des broches en sortie avec pinMode() et la génération de signaux carrés avec digitalWrite().",
            theory=(
                "### Sorties Numériques sous Arduino C/C++\n\n"
                "La carte Arduino Uno possède 14 broches numériques (0 à 13).\n"
                "Le point d'entrée d'un croquis Arduino repose sur deux fonctions indispensables :\n\n"
                "```cpp\n"
                "const int LED_PIN = 13;\n\n"
                "void setup() {\n"
                "  // Exécuté une seule fois à l'initialisation\n"
                "  pinMode(LED_PIN, OUTPUT); // Configure la broche 13 en sortie\n"
                "}\n\n"
                "void loop() {\n"
                "  // Répété indéfiniment en boucle continue\n"
                "  digitalWrite(LED_PIN, HIGH); // Niveau haut (+5V) : allume la LED\n"
                "  delay(1000);                 // Pause de 1000 millisecondes\n"
                "  digitalWrite(LED_PIN, LOW);  // Niveau bas (0V) : éteint la LED\n"
                "  delay(1000);\n"
                "}\n"
                "```\n\n"
                "La broche 13 est directement reliée à la LED miniature 'L' intégrée au circuit imprimé de la carte."
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Insérez une **LED Rouge** et une **Résistance 220Ω** sur la platine d'essai.\n"
                "2. Reliez l'anode à la broche **D13** de l'Arduino Uno et la cathode au **GND** via la résistance.\n"
                "3. Complétez `setup()` et `loop()` pour faire clignoter la LED avec une cadence de 1 seconde (1s ON, 1s OFF).\n"
                "4. Lancez la simulation puis cliquez sur **« ✅ Évaluer mon travail »**."
            ),
            required_components=["led", "resistor"],
            target_pin=13,
            starter_project=create_uno_blink_example(),
            board_id="arduino_uno",
            language="arduino_c"
        ),
        Lesson(
            id="uno_lesson_2_button",
            chapter_num=2,
            chapter_title="Chapitre 2 : Entrées Numériques & Pull-up (C++ Arduino)",
            title="TP 2 (Uno) : Entrées Numériques & Bouton-Poussoir",
            summary="Apprenez à lire l'état d'un bouton poussoir en exploitant la résistance de tirage interne INPUT_PULLUP.",
            theory=(
                "### Entrées Numériques et Résistance Interne de Tirage\n\n"
                "Une broche configurée en entrée simple (`INPUT`) sans résistance flotte et capte du bruit parasite.\n"
                "L'Arduino Uno dispose de résistances de tirage intégrées de 20kΩ à 50kΩ activables par logiciel :\n\n"
                "```cpp\n"
                "const int BTN_PIN = 2;\n"
                "const int LED_PIN = 13;\n\n"
                "void setup() {\n"
                "  pinMode(BTN_PIN, INPUT_PULLUP); // Tirage vers le +5V\n"
                "  pinMode(LED_PIN, OUTPUT);\n"
                "}\n\n"
                "void loop() {\n"
                "  int etat = digitalRead(BTN_PIN);\n"
                "  // Quand le bouton est pressé, il tire la broche à la masse (LOW)\n"
                "  if (etat == LOW) {\n"
                "    digitalWrite(LED_PIN, HIGH); // Allume la LED\n"
                "  } else {\n"
                "    digitalWrite(LED_PIN, LOW);\n"
                "  }\n"
                "}\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez un **Bouton-Poussoir** entre la broche **D2** et la masse **GND**.\n"
                "2. Configurez D2 avec `pinMode(2, INPUT_PULLUP)` dans `setup()`.\n"
                "3. Programmez la boucle pour que la LED s'allume instantanément quand le bouton est maintenu pressé."
            ),
            required_components=["button", "led"],
            target_pin=2,
            starter_project=create_uno_button_led_example(),
            board_id="arduino_uno",
            language="arduino_c"
        ),
        Lesson(
            id="uno_lesson_3_pot_adc",
            chapter_num=3,
            chapter_title="Chapitre 3 : Entrées Analogiques & ADC (C++ Arduino)",
            title="TP 3 (Uno) : Lecture Analogique sur A0 (ADC 10 bits)",
            summary="Convertissez une tension analogique 0-5V en valeur numérique entière de 0 à 1023 avec analogRead().",
            theory=(
                "### Le Convertisseur Analogique-Numérique (ADC) de l'Arduino Uno\n\n"
                "Les broches **A0 à A5** sont raccordées à un convertisseur ADC 10 bits :\n\n"
                "- $0\\text{ V} \\rightarrow 0$\n"
                "- $5\\text{ V} \\rightarrow 1023$\n\n"
                "```cpp\n"
                "void setup() {\n"
                "  Serial.begin(9600); // Initialise la liaison série virtuelle\n"
                "}\n\n"
                "void loop() {\n"
                "  int val = analogRead(A0); // Valeur de 0 à 1023\n"
                "  float tension = val * (5.0 / 1023.0);\n"
                "  Serial.print(\"Valeur brute : \");\n"
                "  Serial.print(val);\n"
                "  Serial.print(\" -> Tension : \");\n"
                "  Serial.print(tension);\n"
                "  Serial.println(\" V\");\n"
                "  delay(200);\n"
                "}\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Câblez un **Potentiomètre** : broche 1 au 5V, broche 3 au GND, et broche curseur (centre) sur **A0**.\n"
                "2. Lisez la valeur analogique et transmettez-la à la console avec `Serial.println()`."
            ),
            required_components=["potentiometer"],
            target_pin=14, # A0 = 14
            starter_project=create_uno_pot_pwm_example(),
            board_id="arduino_uno",
            language="arduino_c"
        ),
        Lesson(
            id="uno_lesson_4_pwm",
            chapter_num=4,
            chapter_title="Chapitre 4 : Modulation de Largeur d'Impulsion (PWM)",
            title="TP 4 (Uno) : Variateur de Lumière PWM sur D9",
            summary="Faites varier la puissance efficace délivrée à une LED avec analogWrite() et la fonction map().",
            theory=(
                "### La Modulation PWM (Pulse Width Modulation)\n\n"
                "Sur Arduino Uno, les broches repérées par un tilde `~` (3, 5, 6, 9, 10, 11) supportent la PWM 8 bits :\n"
                "- `analogWrite(pin, 0)` : 0% de cycle de travail (éteint)\n"
                "- `analogWrite(pin, 128)` : 50% de cycle de travail (demi-luminosité)\n"
                "- `analogWrite(pin, 255)` : 100% de cycle de travail (pleine puissance)\n\n"
                "```cpp\n"
                "const int LED_PIN = 9;\n\n"
                "void setup() {\n"
                "  pinMode(LED_PIN, OUTPUT);\n"
                "}\n\n"
                "void loop() {\n"
                "  int val_adc = analogRead(A0);            // 0 .. 1023\n"
                "  int pwm = map(val_adc, 0, 1023, 0, 255); // Redimensionnement 0 .. 255\n"
                "  analogWrite(LED_PIN, pwm);\n"
                "  delay(50);\n"
                "}\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Reliez une LED à la broche PWM **D9** via sa résistance.\n"
                "2. Utilisez la valeur lue sur le potentiomètre (A0) pour piloter la luminosité de la LED avec `analogWrite(9, ...)`."
            ),
            required_components=["potentiometer", "led", "resistor"],
            target_pin=9,
            starter_project=create_uno_pot_pwm_example(),
            board_id="arduino_uno",
            language="arduino_c"
        ),
        Lesson(
            id="uno_lesson_5_servo",
            chapter_num=5,
            chapter_title="Chapitre 5 : Actionneurs & Bibliothèque Servo",
            title="TP 5 (Uno) : Pilotage de Servomoteur SG90 (Servo.h)",
            summary="Contrôlez l'angle de positionnement d'un servomoteur avec la bibliothèque standard Servo.",
            theory=(
                "### Commande de Servomoteur avec Servo.h\n\n"
                "La bibliothèque officielle `#include <Servo.h>` génère le signal PPM à 50 Hz nécessaire au moteur :\n\n"
                "```cpp\n"
                "#include <Servo.h>\n\n"
                "Servo monServo;\n\n"
                "void setup() {\n"
                "  monServo.attach(9); // Associe l'objet à la broche numérique D9\n"
                "}\n\n"
                "void loop() {\n"
                "  monServo.write(0);   // Positionne à 0 degré\n"
                "  delay(1000);\n"
                "  monServo.write(90);  // Positionne à 90 degrés (centre)\n"
                "  delay(1000);\n"
                "  monServo.write(180); // Positionne à 180 degrés\n"
                "  delay(1000);\n"
                "}\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Branchez le signal du servomoteur sur **D9**, VCC sur **5V** et GND sur **GND**.\n"
                "2. Écrivez un balayage aller-retour fluide entre 0° et 180° avec une boucle `for`."
            ),
            required_components=["servo"],
            target_pin=9,
            starter_project=create_uno_servo_example(),
            board_id="arduino_uno",
            language="arduino_c"
        ),
        Lesson(
            id="uno_lesson_6_traffic_lights",
            chapter_num=6,
            chapter_title="Chapitre 6 : Automatismes & Cycles Temporels",
            title="TP 6 (Uno) : Feux Tricolores de Carrefour Routier",
            summary="Programmez un cycle complet de signalisation tricolore avec trois sorties indépendantes.",
            theory=(
                "### Conception d'un Automatisme à Séquences Temporelles\n\n"
                "Chaque état du carrefour est caractérisé par une combinaison de sorties et une durée déterminée :\n\n"
                "- **Phase 1** : Feu Vert (D10) actif pendant 3 secondes\n"
                "- **Phase 2** : Feu Jaune (D11) actif pendant 1 seconde\n"
                "- **Phase 3** : Feu Rouge (D12) actif pendant 3 secondes\n\n"
                "```cpp\n"
                "const int V = 10, J = 11, R = 12;\n\n"
                "void setup() {\n"
                "  pinMode(V, OUTPUT); pinMode(J, OUTPUT); pinMode(R, OUTPUT);\n"
                "}\n\n"
                "void loop() {\n"
                "  digitalWrite(V, HIGH); delay(3000); digitalWrite(V, LOW);\n"
                "  digitalWrite(J, HIGH); delay(1000); digitalWrite(J, LOW);\n"
                "  digitalWrite(R, HIGH); delay(3000); digitalWrite(R, LOW);\n"
                "}\n"
                "```"
            ),
            challenge=(
                "**Consigne de l'exercice :**\n"
                "1. Connectez 3 LEDs (Verte sur D10, Jaune sur D11, Rouge sur D12) avec résistances.\n"
                "2. Programmez le cycle automatisé des feux routiers et observez le déroulement sur la scène."
            ),
            required_components=["led", "resistor"],
            target_pin=10,
            starter_project=create_uno_traffic_lights_example(),
            board_id="arduino_uno",
            language="arduino_c"
        ),
    ]


def get_course_curriculum(board_id: str | None = None) -> list[Lesson]:
    if board_id in ("arduino_uno", "uno"):
        return get_uno_curriculum()
    elif board_id in ("esp32", "esp32_wroom_32"):
        return get_esp32_curriculum()
    # Par défaut : retourne l'ensemble (ESP32 d'abord pour rétrocompatibilité exacte, puis Uno)
    return get_esp32_curriculum() + get_uno_curriculum()

