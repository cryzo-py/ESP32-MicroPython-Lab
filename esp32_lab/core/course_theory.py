"""
Cours officiel complet : Robotique & Systèmes Connectés ESP32 avec MicroPython
Conforme aux référentiels pédagogiques de programmation et robotique.
"""

from dataclasses import dataclass
from .models.component import ComponentModel
from .models.connection import ConnectionModel
from .models.project import ProjectModel


@dataclass
class TheorySection:
    id: str
    title: str
    icon: str
    summary: str
    content_html: str
    starter_project: ProjectModel | None = None


@dataclass
class TheoryChapter:
    id: str
    number: int
    title: str
    icon: str
    summary: str
    sections: list[TheorySection]


def create_barrier_project() -> ProjectModel:
    """Projet officiel : Barrière automatique (Ultrason HC-SR04 + Servomoteur SG90 + LEDs)"""
    code = '''# PROJET OFFICIEL : BARRIÈRE DE PARKING AUTOMATIQUE
# Capteur : HC-SR04 (Ultrason sur GPIO 5 et 18)
# Actionneurs : Servomoteur SG90 (GPIO 13), LED Verte (GPIO 2), LED Rouge (GPIO 4)

from machine import Pin, PWM, time_pulse_us
from time import sleep, sleep_us

# 1. Configuration des broches d'Entrée / Sortie
trig = Pin(5, Pin.OUT)
echo = Pin(18, Pin.IN)
led_verte = Pin(2, Pin.OUT)
led_rouge = Pin(4, Pin.OUT)

# Configuration du Servomoteur SG90 (PWM à 50 Hz sur GPIO 13)
servo = PWM(Pin(13), freq=50)

def set_angle(angle):
    # Conversion de l'angle (0° à 90°) en rapport cyclique PWM (duty)
    duty = int(25 + (angle / 180.0) * 100)
    servo.duty(duty)

def mesurer_distance():
    trig.value(0)
    sleep_us(2)
    trig.value(1)
    sleep_us(10)
    trig.value(0)
    duree = time_pulse_us(echo, 1, 30000)
    if duree < 0:
        return 100.0  # Pas d'obstacle proche
    return (duree * 0.0343) / 2

print("=== Système de Barrière Automatique Prêt ===")
set_angle(0)  # Barrière baissée par défaut
led_rouge.value(1)
led_verte.value(0)

while True:
    distance = mesurer_distance()
    print("Distance mesurée :", round(distance, 1), "cm")

    # Prise de décision : obstacle détecté à moins de 20 cm
    if distance < 20:
        print(">> Véhicule détecté ! Ouverture de la barrière...")
        led_rouge.value(0)
        led_verte.value(1)
        set_angle(90)  # Lever la barrière à 90°
        sleep(4)       # Temps de passage du véhicule
        print(">> Fermeture de la barrière...")
        set_angle(0)   # Rabaisser la barrière à 0°
        led_verte.value(0)
        led_rouge.value(1)
    else:
        # Voie libre, barrière fermée
        set_angle(0)
        led_rouge.value(1)
        led_verte.value(0)

    sleep(0.5)
'''
    project = ProjectModel(
        name="Projet Officiel : Barrière Automatique",
        description="Barrière de parking intelligente avec détection d'obstacle par ultrason et levée de barrière par servomoteur.",
        files={"main.py": code},
        components=[
            ComponentModel(id="esp32", type="esp32", x=300, y=100),
            ComponentModel(id="hcsr04", type="hcsr04", x=100, y=120),
            ComponentModel(id="servo", type="servo", x=550, y=120),
            ComponentModel(id="led_v", type="led", x=300, y=360, properties={"color": "green"}),
            ComponentModel(id="led_r", type="led", x=420, y=360, properties={"color": "red"}),
        ],
        connections=[
            ConnectionModel(id="w1", from_component="hcsr04", from_pin="trig", to_component="esp32", to_pin="GPIO5", color="#3b82f6"),
            ConnectionModel(id="w2", from_component="hcsr04", from_pin="echo", to_component="esp32", to_pin="GPIO18", color="#06b6d4"),
            ConnectionModel(id="w3", from_component="hcsr04", from_pin="vcc", to_component="esp32", to_pin="VIN", color="#ef4444"),
            ConnectionModel(id="w4", from_component="hcsr04", from_pin="gnd", to_component="esp32", to_pin="GND_1", color="#0f172a"),
            ConnectionModel(id="w5", from_component="servo", from_pin="sig", to_component="esp32", to_pin="GPIO13", color="#f97316"),
            ConnectionModel(id="w6", from_component="servo", from_pin="vcc", to_component="esp32", to_pin="VIN", color="#ef4444"),
            ConnectionModel(id="w7", from_component="servo", from_pin="gnd", to_component="esp32", to_pin="GND_1", color="#0f172a"),
            ConnectionModel(id="w8", from_component="led_v", from_pin="anode", to_component="esp32", to_pin="GPIO2", color="#22c55e"),
            ConnectionModel(id="w9", from_component="led_v", from_pin="cathode", to_component="esp32", to_pin="GND_2", color="#0f172a"),
            ConnectionModel(id="w10", from_component="led_r", from_pin="anode", to_component="esp32", to_pin="GPIO4", color="#ef4444"),
            ConnectionModel(id="w11", from_component="led_r", from_pin="cathode", to_component="esp32", to_pin="GND_2", color="#0f172a"),
        ]
    )
    return project


def create_irrigation_project() -> ProjectModel:
    """Projet officiel : Système d'arrosage automatique (Capteur DHT22 + Module Relais)"""
    code = '''# PROJET OFFICIEL : SYSTÈME D'ARROSAGE AUTOMATIQUE
# Capteur : DHT22 (Température et Humidité sur GPIO 4)
# Actionneurs : Module Relais de puissance (GPIO 5), Voyant LED (GPIO 2)

from machine import Pin
from time import sleep
import dht

# 1. Initialisation des composants
capteur = dht.DHT22(Pin(4))
relais_pompe = Pin(5, Pin.OUT)
temoin_arrosage = Pin(2, Pin.OUT)

# État initial : pompe arrêtée
relais_pompe.value(0)
temoin_arrosage.value(0)
SEUIL_HUMIDITE = 45.0  # Pourcentage d'humidité seuil

print("=== Système d'Arrosage Automatique Démarré ===")

while True:
    try:
        # Mesure des grandeurs physiques de l'environnement
        capteur.measure()
        temperature = capteur.temperature()
        humidite = capteur.humidity()

        print("Temp :", temperature, "°C | Humidité :", humidite, "%")

        # Traitement et Prise de décision automatique
        if humidite < SEUIL_HUMIDITE:
            print(">> ALERTE : Sol trop sec ! Démarrage de la pompe...")
            relais_pompe.value(1)     # Enclenche le relais (contact fermé)
            temoin_arrosage.value(1)  # Allume le voyant
        else:
            print(">> Humidité suffisante. Pompe au repos.")
            relais_pompe.value(0)     # Coupe le relais (contact ouvert)
            temoin_arrosage.value(0)  # Éteint le voyant

    except OSError as e:
        print("Erreur de lecture du capteur :", e)

    sleep(2)
'''
    project = ProjectModel(
        name="Projet Officiel : Arrosage Automatique",
        description="Surveillance de l'humidité et température par capteur DHT22 et enclenchement d'une pompe d'arrosage via un module Relais.",
        files={"main.py": code},
        components=[
            ComponentModel(id="esp32", type="esp32", x=300, y=100),
            ComponentModel(id="dht22", type="dht22", x=100, y=140),
            ComponentModel(id="relay", type="relay", x=550, y=140),
            ComponentModel(id="led", type="led", x=300, y=360, properties={"color": "blue"}),
        ],
        connections=[
            ConnectionModel(id="w1", from_component="dht22", from_pin="data", to_component="esp32", to_pin="GPIO4", color="#3b82f6"),
            ConnectionModel(id="w2", from_component="dht22", from_pin="vcc", to_component="esp32", to_pin="3V3", color="#ef4444"),
            ConnectionModel(id="w3", from_component="dht22", from_pin="gnd", to_component="esp32", to_pin="GND_1", color="#0f172a"),
            ConnectionModel(id="w4", from_component="relay", from_pin="in", to_component="esp32", to_pin="GPIO5", color="#f59e0b"),
            ConnectionModel(id="w5", from_component="relay", from_pin="vcc", to_component="esp32", to_pin="VIN", color="#ef4444"),
            ConnectionModel(id="w6", from_component="relay", from_pin="gnd", to_component="esp32", to_pin="GND_1", color="#0f172a"),
            ConnectionModel(id="w7", from_component="led", from_pin="anode", to_component="esp32", to_pin="GPIO2", color="#38bdf8"),
            ConnectionModel(id="w8", from_component="led", from_pin="cathode", to_component="esp32", to_pin="GND_2", color="#0f172a"),
        ]
    )
    return project


def get_official_course_curriculum() -> list[TheoryChapter]:
    """Retourne la totalité des 5 chapitres du cours officiel formattés pour QTextBrowser."""
    return [
        TheoryChapter(
            id="chap1_intro_robotique",
            number=1,
            title="Introduction à la Robotique & Objets Connectés",
            icon="🤖",
            summary="Définition de la robotique, domaines d'application industrielle et concept fondamental d'objet connecté (IoT).",
            sections=[
                TheorySection(
                    id="sec1_1_definition",
                    title="1.1 Qu'est-ce que la Robotique ?",
                    icon="🎯",
                    summary="Comprendre les 3 piliers fondamentaux : Percevoir, Traiter, Agir.",
                    content_html=(
                        "<h2>1.1 Qu'est-ce que la Robotique ?</h2>"
                        "<p>La <b>robotique</b> est un domaine pluridisciplinaire combinant la mécanique, l'électronique et l'informatique. "
                        "Un système robotique ou automatisé a pour vocation d'accomplir des tâches de manière autonome ou semi-autonome.</p>"
                        "<div style='background-color: rgba(14, 165, 233, 0.1); border-left: 4px solid #0ea5e9; padding: 12px; margin: 12px 0; border-radius: 4px;'>"
                        "<b>Le Cycle Fondamental d'un Robot :</b><br>"
                        "1. <b>Percevoir :</b> Mesurer des grandeurs physiques grâce à des <i>capteurs</i>.<br>"
                        "2. <b>Décider / Traiter :</b> Analyser les données et exécuter un algorithme grâce à une <i>unité de traitement</i> (microcontrôleur).<br>"
                        "3. <b>Agir :</b> Produire un effet tangible sur le monde réel grâce à des <i>actionneurs</i> (moteurs, vérins, lumières)."
                        "</div>"
                        "<p>Sans programme informatique, un robot n'est qu'un ensemble de métal et de plastique inerte. Le programme constitue le <b>cerveau décisionnel</b> du système.</p>"
                    )
                ),
                TheorySection(
                    id="sec1_2_domaines",
                    title="1.2 Domaines d'application dans la société",
                    icon="🌍",
                    summary="Les secteurs majeurs : industrie, domotique, santé, agriculture et logistique.",
                    content_html=(
                        "<h2>1.2 Les Domaines d'Application de la Robotique</h2>"
                        "<p>Aujourd'hui, la robotique et les objets intelligents transforment l'ensemble des activités humaines :</p>"
                        "<ul>"
                        "<li><b>Industrie et Production :</b> Lignes d'assemblage automatisées, bras robotiques de soudage et de peinture, découpe laser haute précision.</li>"
                        "<li><b>Logistique & Transport :</b> Robots mobiles autonomes (AGV) dans les entrepôts logistiques, véhicules à pilotage automatique, drones de livraison.</li>"
                        "<li><b>Domotique & Bâtiment intelligent :</b> Aspirateurs et tondeuses autonomes, gestion intelligente du chauffage et de l'éclairage, barrières et volets motorisés.</li>"
                        "<li><b>Santé & Chirurgie :</b> Robots chirurgicaux téléopérés permettant des incisions millimétriques, prothèses bioniques motorisées.</li>"
                        "<li><b>Agriculture connectée :</b> Surveillance des parcelles par capteurs météo, arrosage ciblé sans gaspillage, désherbage mécanique automatique.</li>"
                        "</ul>"
                    )
                ),
                TheorySection(
                    id="sec1_3_iot",
                    title="1.3 Qu'est-ce qu'un Objet Connecté (IoT) ?",
                    icon="🌐",
                    summary="L'Internet des Objets : connecter le monde physique aux réseaux numériques.",
                    content_html=(
                        "<h2>1.3 Qu'est-ce qu'un Objet Connecté (IoT) ?</h2>"
                        "<p>L'<b>Internet des Objets</b> (<i>Internet of Things - IoT</i>) désigne l'ensemble des équipements physiques connectés "
                        "à un réseau informatique (local ou mondial), capables de collecter des données et de communiquer sans intervention humaine directe.</p>"
                        "<div style='background-color: rgba(34, 197, 94, 0.1); border-left: 4px solid #22c55e; padding: 12px; margin: 12px 0; border-radius: 4px;'>"
                        "<b>Exemples du quotidien :</b><br>"
                        "• Une <b>station météo autonome</b> qui publie ses mesures de température sur une page web.<br>"
                        "• Une <b>barrière de parking</b> qui s'ouvre à distance ou envoie une notification d'accès.<br>"
                        "• Un <b>système d'arrosage connecté</b> qui consulte les prévisions météorologiques avant d'arroser."
                        "</div>"
                        "<p>L'apprenant n'a pas besoin de concevoir une application mobile complexe : la programmation du microcontrôleur lui-même suffit à donner vie à l'objet.</p>"
                    )
                )
            ]
        ),
        TheoryChapter(
            id="chap2_anatomie_esp32",
            number=2,
            title="Anatomie & Matériel de la Carte ESP32",
            icon="⚡",
            summary="Unité de traitement, mémoires SRAM/Flash, communications Wi-Fi/Bluetooth et caractéristiques des broches GPIO 3.3V.",
            sections=[
                TheorySection(
                    id="sec2_1_chainefonctionnelle",
                    title="2.1 Les 4 Composants Matériels Essentiels",
                    icon="🧩",
                    summary="Entrées, Unité de traitement, Sorties et Moyens de communication.",
                    content_html=(
                        "<h2>2.1 Les 4 Composants Matériels Essentiels d'un Objet Connecté</h2>"
                        "<p>Conformément aux directives pédagogiques officielles, tout objet connecté est constitué de 4 sous-ensembles majeurs :</p>"
                        "<table border='1' cellspacing='0' cellpadding='8' style='border-collapse:collapse; width:100%; border:1px solid #94a3b8;'>"
                        "<tr style='background-color: rgba(56, 189, 248, 0.15); font-weight:bold;'>"
                        "<td>Sous-ensemble</td><td>Rôle technique</td><td>Exemples concrets</td>"
                        "</tr>"
                        "<tr>"
                        "<td><b>1. Entrées (Capteurs)</b></td>"
                        "<td>Captent une grandeur physique de l'environnement pour la transformer en signal électrique.</td>"
                        "<td>Bouton poussoir, Capteur DHT22 (température/humidité), Capteur ultrason HC-SR04, Potentiomètre.</td>"
                        "</tr>"
                        "<tr>"
                        "<td><b>2. Unité de traitement</b></td>"
                        "<td>Exécute le code informatique, effectue les calculs et prend les décisions.</td>"
                        "<td>Microcontrôleur <b>ESP32</b> (processeur 32-bit double cœur).</td>"
                        "</tr>"
                        "<tr>"
                        "<td><b>3. Sorties (Actionneurs)</b></td>"
                        "<td>Transforment l'ordre de commande en action physique.</td>"
                        "<td>LED (lumière), Servomoteur SG90 (mouvement angulaire), Relais (commutation de puissance), Écran OLED.</td>"
                        "</tr>"
                        "<tr>"
                        "<td><b>4. Moyens de communication</b></td>"
                        "<td>Échangent des informations sans fil à courte ou longue portée.</td>"
                        "<td><b>Wi-Fi</b> (802.11 b/g/n) et <b>Bluetooth</b> intégrés directement dans la puce ESP32.</td>"
                        "</tr>"
                        "</table>"
                    )
                ),
                TheorySection(
                    id="sec2_2_memoires",
                    title="2.2 Unité de Traitement & Mémoires (SRAM vs Flash)",
                    icon="💾",
                    summary="Comprendre le rôle de la mémoire vive (SRAM) et du stockage permanent (Flash).",
                    content_html=(
                        "<h2>2.2 Le Cœur de l'ESP32 : Processeur et Mémoires</h2>"
                        "<p>La carte ESP32 embarque un microprocesseur <b>Xtensa LX6 32-bit double cœur</b> pouvant tourner à une fréquence de 240 MHz.</p>"
                        "<h3>Distinction essentielle entre les deux mémoires :</h3>"
                        "<ul>"
                        "<li><b>Mémoire SRAM (520 Ko - Volatile) :</b><br>"
                        "C'est la mémoire de travail (RAM). Elle conserve les variables actives et l'exécution du code. Dès que l'ESP32 est éteint ou redémarré, son contenu est effacé.</li>"
                        "<li><b>Mémoire Flash (4 Mo à 16 Mo - Non Volatile) :</b><br>"
                        "C'est le disque dur de la carte. Elle conserve le système d'exploitation MicroPython ainsi que vos fichiers de code (<code>main.py</code>). "
                        "Le programme y reste gravé même après coupure totale de l'alimentation.</li>"
                        "</ul>"
                    )
                ),
                TheorySection(
                    id="sec2_3_gpio",
                    title="2.3 Les Broches GPIO & La Règle d'Or du 3.3V",
                    icon="⚠️",
                    summary="Attribution des broches, limitation en courant et protection électrique absolue.",
                    content_html=(
                        "<h2>2.3 Les Broches GPIO (General Purpose Input/Output)</h2>"
                        "<p>Les broches permettent à l'ESP32 de communiquer avec le monde extérieur.</p>"
                        "<div style='background-color: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 12px; margin: 12px 0; border-radius: 4px;'>"
                        "⚠️ <b>RÈGLE DE SÉCURITÉ ABSOLUE : NIVEAU LOGIQUE 3.3V</b><br>"
                        "L'ESP32 fonctionne sous une tension logique de <b>3.3V</b>. N'appliquez JAMAIS directement du 5V sur une broche d'entrée GPIO, "
                        "sous peine de détruire irrémédiablement le processeur !"
                        "</div>"
                        "<h3>Types de broches à retenir :</h3>"
                        "<ul>"
                        "<li><b>Broches polyvalentes (Entrées / Sorties) :</b> GPIO 2, 4, 5, 12, 13, 14, 15, 18, 19, 21, 22, 23.</li>"
                        "<li><b>Broches d'ENTRÉE SEULE (Input Only) :</b> GPIO 34, 35, 36 (VP), 39 (VN). Elles ne peuvent pas être configurées en sortie et ne possèdent pas de résistance pull-up interne.</li>"
                        "<li><b>Broche LED intégrée :</b> Sur la plupart des cartes de développement ESP32, une LED bleue interne est reliée au <b>GPIO 2</b>.</li>"
                        "</ul>"
                    )
                )
            ]
        ),
        TheoryChapter(
            id="chap3_micropython_prog",
            number=3,
            title="Du Visuel au Textuel avec MicroPython",
            icon="💻",
            summary="Passer de Scratch à Python : types de données simples (int, float, bool, str) et structures de contrôle directes.",
            sections=[
                TheorySection(
                    id="sec3_1_transition",
                    title="3.1 Pourquoi MicroPython pour la Robotique ?",
                    icon="🐍",
                    summary="Les avantages d'un langage textuel épuré et immédiatement interprété.",
                    content_html=(
                        "<h2>3.1 Pourquoi MicroPython ?</h2>"
                        "<p>Après avoir appris la logique de programmation avec des blocs visuels (comme Scratch ou Blockly), "
                        "la programmation textuelle permet d'accéder au véritable monde de l'ingénierie et de l'IoT.</p>"
                        "<p><b>MicroPython</b> est une réimplémentation complète de Python 3 conçue pour les microcontrôleurs :</p>"
                        "<ul>"
                        "<li>Code concis, lisible et très proche du langage naturel.</li>"
                        "<li>Pas de compilation lourde : le code est exécuté directement sur la carte.</li>"
                        "<li>Des bibliothèques matérielles simples : le module <code>machine</code> permet de contrôler les broches en 2 lignes !</li>"
                        "</ul>"
                    )
                ),
                TheorySection(
                    id="sec3_2_types",
                    title="3.2 Les Variables & Les 4 Types Simples",
                    icon="🔢",
                    summary="Entiers, Flottants, Booléens et Chaînes de caractères.",
                    content_html=(
                        "<h2>3.2 Les Types de Données Simples</h2>"
                        "<p>Une variable est une boîte étiquetée dans la mémoire de l'ESP32. En robotique, on manipule 4 types fondamentaux :</p>"
                        "<pre style='background: rgba(0,0,0,0.06); padding: 10px; border-radius: 6px; font-family: Consolas, monospace;'>"
                        "# 1. Entier (int) : nombre sans virgule (état broche, angle, compteur)\n"
                        "broche_led = 2\n"
                        "angle_servo = 90\n\n"
                        "# 2. Flottant (float) : nombre à virgule (mesures physiques)\n"
                        "temperature = 23.8\n"
                        "distance_cm = 14.5\n\n"
                        "# 3. Booléen (bool) : Vrai (True) ou Faux (False)\n"
                        "obstacle_detecte = True\n"
                        "porte_ouverte = False\n\n"
                        "# 4. Chaîne de caractères (str) : texte entre guillemets\n"
                        "message = \"Acces Autorise\"\n"
                        "</pre>"
                    )
                ),
                TheorySection(
                    id="sec3_3_structures",
                    title="3.3 Les Structures de Contrôle Élémentaires",
                    icon="🔀",
                    summary="Séquence, Décision simple (if / else) et Boucle de scrutation infinie (while True).",
                    content_html=(
                        "<h2>3.3 Structures de Contrôle Fondamentales</h2>"
                        "<p><i>Rappel de la directive pédagogique officielle : utiliser des structures de contrôle simples et directes, sans imbrications complexes.</i></p>"
                        "<h3>1. La Séquence Linéaire :</h3>"
                        "<p>Les instructions sont exécutées l'une après l'autre de haut en bas.</p>"
                        "<h3>2. La Prise de Décision Simple (<code>if / else</code>) :</h3>"
                        "<p>Permet à l'objet connecté de choisir son action en fonction d'un événement capteur :</p>"
                        "<pre style='background: rgba(0,0,0,0.06); padding: 10px; border-radius: 6px; font-family: Consolas, monospace;'>"
                        "if distance < 15:\n"
                        "    print(\"Obstacle proche : Action requise !\")\n"
                        "else:\n"
                        "    print(\"Voie dégagée : Tout est normal.\")\n"
                        "</pre>"
                        "<h3>3. La Boucle Infinie (<code>while True</code>) :</h3>"
                        "<p>Un objet connecté ne s'arrête jamais : il surveille ses capteurs en continu dans une boucle perpétuelle cadencée par des pauses (<code>sleep</code>).</p>"
                    )
                )
            ]
        ),
        TheoryChapter(
            id="chap4_chaine_capteur_actionneur",
            number=4,
            title="La Chaîne Capteur ➔ Traitement ➔ Actionneur",
            icon="🔄",
            summary="Règle d'or officielle : toujours associer au moins un capteur pour lire des données et au moins un actionneur pour réagir.",
            sections=[
                TheorySection(
                    id="sec4_1_capteurs",
                    title="4.1 Les Capteurs d'Entrée Usuels",
                    icon="📡",
                    summary="DHT22 (température/humidité), HC-SR04 (ultrason), Boutons et Potentiomètres.",
                    content_html=(
                        "<h2>4.1 Les Capteurs : Recueillir l'Information</h2>"
                        "<p>Le capteur transforme une grandeur physique en grandeur électrique assimilable par l'ESP32 :</p>"
                        "<ul>"
                        "<li><b>Bouton Poussoir :</b> Entrée numérique Tout-Ou-Rien (0V ou 3.3V). Nécessite une résistance de rappel (Pull-Up ou Pull-Down).</li>"
                        "<li><b>Capteur DHT22 :</b> Transmet la température et l'humidité via une trame numérique 1-wire sur une seule broche GPIO.</li>"
                        "<li><b>Capteur Ultrason HC-SR04 :</b> Émet une impulsion sonore (Trig) et mesure le temps de retour (Echo).<br>"
                        "Formule de calcul : <code>Distance (cm) = (Temps en microsecondes × 0.0343) / 2</code></li>"
                        "<li><b>Potentiomètre (Entrée Analogique ADC) :</b> Fournit une tension progressive entre 0V et 3.3V, convertie en valeur numérique de 0 à 4095 (résolution 12 bits).</li>"
                        "</ul>"
                    )
                ),
                TheorySection(
                    id="sec4_2_actionneurs",
                    title="4.2 Les Actionneurs de Sortie Usuels",
                    icon="⚙️",
                    summary="Servomoteur SG90 (mouvement angulaire), Relais (puissance), LED et Écrans.",
                    content_html=(
                        "<h2>4.2 Les Actionneurs : Agir sur l'Environnement</h2>"
                        "<p>L'actionneur reçoit un ordre électrique de l'ESP32 et génère une action concrète :</p>"
                        "<ul>"
                        "<li><b>LED (Diode Électroluminescente) :</b> Signal visuel. Doit impérativement être accompagnée d'une résistance de limitation (220 Ω) pour ne pas griller.</li>"
                        "<li><b>Servomoteur SG90 :</b> Moteur commandé en PWM (50 Hz) permettant de positionner un bras ou une barrière à un angle précis de 0° à 180°.</li>"
                        "<li><b>Module Relais Électromécanique :</b> Permet au faible signal 3.3V de l'ESP32 d'enclencher ou couper un circuit externe de forte puissance (pompe à eau 12V, moteur 220V, électrovanne).</li>"
                        "<li><b>Afficheurs (OLED SSD1306 / LCD 16x2) :</b> Communiquent via le bus I2C (2 fils SDA/SCL) pour afficher des valeurs textuelles ou graphiques.</li>"
                        "</ul>"
                    )
                )
            ]
        ),
        TheoryChapter(
            id="chap5_projets_officiels",
            number=5,
            title="Les Grands Projets d'Application Officiels",
            icon="🏆",
            summary="Les deux projets types imposés par les directives pédagogiques : La Barrière Automatique et Le Système d'Arrosage Automatique.",
            sections=[
                TheorySection(
                    id="sec5_1_barriere",
                    title="5.1 Projet Officiel : La Barrière Automatique",
                    icon="🚗",
                    summary="Détection d'obstacle par ultrason HC-SR04 et ouverture de barrière par Servomoteur SG90 avec voyants de signalisation.",
                    content_html=(
                        "<h2>5.1 Projet Type 1 : La Barrière de Parking Automatique</h2>"
                        "<p><i>Ce projet est explicitement préconisé par les directives officielles pour valider la chaîne Capteur ➔ Traitement ➔ Actionneur.</i></p>"
                        "<div style='background-color: rgba(56, 189, 248, 0.1); border-left: 4px solid #38bdf8; padding: 12px; margin: 12px 0; border-radius: 4px;'>"
                        "<b>Cahier des charges :</b><br>"
                        "• Un véhicule s'approche de la barrière de parking.<br>"
                        "• Le capteur ultrason détecte sa présence lorsque la distance est inférieure à <b>20 cm</b>.<br>"
                        "• Le feu passe du <b>Rouge (GPIO 4)</b> au <b>Vert (GPIO 2)</b>.<br>"
                        "• Le servomoteur SG90 (GPIO 13) lève la barrière à <b>90°</b>.<br>"
                        "• Après 4 secondes d'attente (passage du véhicule), la barrière redescend à <b>0°</b> et le feu redevient Rouge."
                        "</div>"
                        "<h3>Code MicroPython du projet :</h3>"
                        "<pre style='background: rgba(0,0,0,0.06); padding: 12px; border-radius: 6px; font-family: Consolas, monospace; font-size: 11px; line-height: 1.4;'>"
                        "# Configuration des broches\n"
                        "trig = Pin(5, Pin.OUT)\n"
                        "echo = Pin(18, Pin.IN)\n"
                        "led_verte = Pin(2, Pin.OUT)\n"
                        "led_rouge = Pin(4, Pin.OUT)\n"
                        "servo = PWM(Pin(13), freq=50)\n\n"
                        "while True:\n"
                        "    distance = mesurer_distance()\n"
                        "    if distance < 20:\n"
                        "        print('Véhicule détecté ! Ouverture...')\n"
                        "        led_rouge.value(0)\n"
                        "        led_verte.value(1)\n"
                        "        set_angle(90)  # Lever la barrière\n"
                        "        sleep(4)\n"
                        "        set_angle(0)   # Rabaisser la barrière\n"
                        "        led_verte.value(0)\n"
                        "        led_rouge.value(1)\n"
                        "    else:\n"
                        "        set_angle(0)\n"
                        "    sleep(0.5)"
                        "</pre>"
                        "<p>Vous pouvez tester ce projet complet et pré-câblé immédiatement dans le simulateur en cliquant sur le bouton ci-dessous !</p>"
                    ),
                    starter_project=create_barrier_project()
                ),
                TheorySection(
                    id="sec5_2_arrosage",
                    title="5.2 Projet Officiel : Système d'Arrosage Automatique",
                    icon="💧",
                    summary="Mesure d'humidité par capteur DHT22 et déclenchement d'une pompe d'irrigation via un module Relais.",
                    content_html=(
                        "<h2>5.2 Projet Type 2 : Le Système d'Arrosage Automatique</h2>"
                        "<p><i>Deuxième grand projet préconisé par le référentiel officiel pour l'agriculture intelligente et la domotique.</i></p>"
                        "<div style='background-color: rgba(34, 197, 94, 0.1); border-left: 4px solid #22c55e; padding: 12px; margin: 12px 0; border-radius: 4px;'>"
                        "<b>Cahier des charges :</b><br>"
                        "• Le capteur DHT22 (GPIO 4) mesure en continu l'humidité de l'environnement.<br>"
                        "• Si l'humidité descend sous le <b>seuil de 45%</b> (sol trop sec) :<br>"
                        "  - L'ESP32 enclenche le <b>Relais (GPIO 5)</b> pour alimenter la pompe à eau.<br>"
                        "  - Le voyant d'arrosage (GPIO 2) s'allume.<br>"
                        "• Dès que l'humidité mesurée remonte au-dessus de 45% :<br>"
                        "  - Le Relais s'ouvre immédiatement pour stopper la pompe.<br>"
                        "  - Le voyant s'éteint pour économiser l'énergie."
                        "</div>"
                        "<h3>Code MicroPython du projet :</h3>"
                        "<pre style='background: rgba(0,0,0,0.06); padding: 12px; border-radius: 6px; font-family: Consolas, monospace; font-size: 11px; line-height: 1.4;'>"
                        "# Surveillance et arrosage automatique\n"
                        "capteur = dht.DHT22(Pin(4))\n"
                        "relais_pompe = Pin(5, Pin.OUT)\n"
                        "temoin_arrosage = Pin(2, Pin.OUT)\n\n"
                        "while True:\n"
                        "    capteur.measure()\n"
                        "    humidite = capteur.humidity()\n"
                        "    if humidite < 45.0:\n"
                        "        print('Sol trop sec ! Démarrage de la pompe...')\n"
                        "        relais_pompe.value(1)     # Pompe ON\n"
                        "        temoin_arrosage.value(1)\n"
                        "    else:\n"
                        "        relais_pompe.value(0)     # Pompe OFF\n"
                        "        temoin_arrosage.value(0)\n"
                        "    sleep(2)"
                        "</pre>"
                        "<p>Vous pouvez charger et exécuter ce circuit pré-câblé en un clic grâce au bouton ci-dessous !</p>"
                    ),
                    starter_project=create_irrigation_project()
                )
            ]
        )
    ]
