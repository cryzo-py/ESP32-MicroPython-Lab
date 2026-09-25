# CAHIER DES CHARGES
## Plateforme de simulation et de programmation ESP32 avec MicroPython

**Nom provisoire du projet :** ESP32 MicroPython Lab  
**Version :** 1.0  
**Type :** Plateforme éducative de programmation, simulation et expérimentation IoT  
**Technologie principale :** MicroPython / ESP32  
**Public cible :** Élèves, étudiants, enseignants, formateurs, makers et développeurs débutants

---

# 1. Présentation générale

## 1.1. Contexte

Le projet consiste à développer une application permettant de programmer une carte ESP32 en **MicroPython**, de simuler son fonctionnement dans un environnement virtuel et, lorsque l'utilisateur dispose d'une carte physique, de transférer le même programme vers celle-ci.

L'objectif est de proposer un environnement intégré évitant à l'utilisateur de devoir utiliser plusieurs logiciels séparés pour :

- écrire son programme ;
- tester son programme ;
- connecter des composants électroniques ;
- observer le comportement du montage ;
- consulter les messages série ;
- corriger les erreurs ;
- transférer le programme vers une ESP32 réelle.

L'application doit donc jouer le rôle d'un **laboratoire ESP32 virtuel et réel**.

---

# 2. Objectifs du projet

## 2.1. Objectif principal

Créer une plateforme dans laquelle l'utilisateur peut passer naturellement du :

**Code → Simulation → Correction → Expérimentation → ESP32 physique**

sans changer d'environnement.

## 2.2. Objectifs pédagogiques

La plateforme doit permettre à un débutant de comprendre progressivement :

- Python ;
- MicroPython ;
- GPIO ;
- entrées/sorties numériques ;
- entrées analogiques ;
- PWM ;
- capteurs ;
- actionneurs ;
- bus I2C ;
- SPI ;
- UART ;
- communication réseau ;
- Wi-Fi ;
- MQTT ;
- principes de l'IoT.

## 2.3. Objectifs techniques

L'application doit notamment permettre :

1. d'écrire du code MicroPython ;
2. de vérifier la syntaxe ;
3. d'exécuter le code dans le simulateur ;
4. de visualiser les résultats ;
5. de connecter virtuellement des composants ;
6. de communiquer avec une ESP32 réelle ;
7. d'envoyer des fichiers/programmes sur la carte ;
8. de récupérer les messages du port série ;
9. d'accéder au REPL MicroPython ;
10. de gérer des projets.

---

# 3. Concept général de l'application

L'application sera organisée autour de quatre environnements principaux.

## 3.1. Éditeur

Permet d'écrire et modifier le programme MicroPython.

Exemple :

```python
from machine import Pin
from time import sleep

led = Pin(2, Pin.OUT)

while True:
    led.value(1)
    sleep(1)
    led.value(0)
    sleep(1)
```

## 3.2. Simulateur

Permet d'exécuter le programme sans disposer d'une carte physique.

Le simulateur représente :

- ESP32 ;
- GPIO ;
- alimentation ;
- LED ;
- boutons ;
- résistances ;
- potentiomètres ;
- capteurs ;
- écrans ;
- servomoteurs ;
- buzzer ;
- etc.

## 3.3. Laboratoire physique

Permet de connecter une ESP32 réelle à l'ordinateur via USB et d'envoyer le programme.

## 3.4. Environnement pédagogique

Permet à l'enseignant de créer :

- cours ;
- exercices ;
- projets ;
- travaux pratiques ;
- évaluations ;
- corrections automatiques.

---

# 4. Utilisateurs

## 4.1. Élève / étudiant

L'élève peut :

- créer un projet ;
- écrire du code ;
- simuler ;
- modifier son montage ;
- sauvegarder son travail ;
- envoyer le programme vers une ESP32 ;
- consulter les résultats ;
- réaliser des exercices.

## 4.2. Enseignant

L'enseignant peut :

- créer des exercices ;
- définir les composants autorisés ;
- fournir un code initial ;
- définir une consigne ;
- définir des tests ;
- suivre les travaux ;
- consulter les résultats ;
- créer des parcours pédagogiques.

## 4.3. Administrateur

L'administrateur peut :

- gérer les utilisateurs ;
- gérer les contenus ;
- gérer les composants ;
- gérer les exercices ;
- gérer les classes ;
- gérer les paramètres de la plateforme.

---

# 5. Interface générale

L'interface devra être moderne, claire et adaptée à l'éducation.

## 5.1. Barre principale

La barre supérieure contiendra :

- Accueil ;
- Éditeur ;
- Simulateur ;
- Téléverser ;
- Cours ;
- Projets ;
- Paramètres ;
- profil utilisateur.

## 5.2. Zone composants

Une bibliothèque de composants sera disponible sur la gauche.

Exemple :

### Composants de base

- LED ;
- résistance ;
- bouton ;
- interrupteur ;
- potentiomètre ;
- buzzer.

### Actionneurs

- servo ;
- moteur DC ;
- relais ;
- RGB LED.

### Capteurs

- température ;
- humidité ;
- luminosité ;
- distance ;
- mouvement ;
- gaz ;
- pression.

### Affichage

- LCD ;
- OLED ;
- TFT ;
- matrice LED.

### Communication

- UART ;
- I2C ;
- SPI ;
- module SD.

---

# 6. Éditeur MicroPython

## 6.1. Fonctionnalités

L'éditeur doit fournir :

- coloration syntaxique ;
- indentation automatique ;
- numérotation des lignes ;
- recherche ;
- remplacement ;
- annulation/rétablissement ;
- copier/coller ;
- gestion de plusieurs fichiers ;
- sauvegarde automatique ;
- détection d'erreurs ;
- messages d'erreur ;
- autocomplétion à terme.

## 6.2. Gestion des fichiers

Un projet peut contenir :

```text
MonProjet/
│
├── main.py
├── boot.py
├── config.py
├── sensors.py
└── lib/
    └── ...
```

L'application doit permettre :

- créer un fichier ;
- supprimer ;
- renommer ;
- déplacer ;
- ouvrir ;
- télécharger ;
- importer.

## 6.3. Fichiers MicroPython particuliers

Le système doit reconnaître notamment :

### boot.py

Code exécuté au démarrage.

### main.py

Programme principal.

---

# 7. Vérification du code

Avant simulation ou téléversement, l'application doit pouvoir effectuer une vérification.

Exemples d'erreurs :

```text
SyntaxError
NameError
IndentationError
ImportError
```

L'erreur doit être associée à :

- numéro de ligne ;
- position ;
- type ;
- message ;
- suggestion de correction lorsque possible.

Exemple :

```text
Erreur ligne 12

IndentationError:
unexpected indent

[Afficher dans l'éditeur]
```

---

# 8. Simulateur ESP32

## 8.1. Objectif

Le simulateur doit reproduire le comportement observable d'une ESP32 utilisée avec MicroPython.

Il ne sera pas nécessaire, dans la première version, de simuler physiquement chaque transistor ou chaque périphérique interne.

La simulation sera basée sur les fonctionnalités MicroPython réellement utilisées par l'utilisateur.

---

# 9. Modèle virtuel ESP32

Le simulateur doit représenter une carte ESP32 avec ses GPIO.

Exemple :

```text
                 ESP32
        ┌───────────────────┐
        │                   │
 GPIO 0 │ ●                 │
 GPIO 2 │ ●────── LED       │
 GPIO 4 │ ●                 │
 GPIO 5 │ ●                 │
 GPIO 18│ ●                 │
 GPIO 19│ ●                 │
 GPIO 21│ ●                 │
 GPIO 22│ ●                 │
 GPIO 23│ ●                 │
        │                   │
        └───────────────────┘
```

Les broches doivent être représentées visuellement.

---

# 10. Simulation GPIO

Le moteur doit supporter notamment :

```python
Pin(2, Pin.OUT)
Pin(4, Pin.IN)
```

et :

```python
pin.value(1)
pin.value(0)
```

ainsi que :

```python
pin.value()
```

Le changement d'état doit être immédiatement visible dans le simulateur.

---

# 11. Simulation LED

Une LED virtuelle doit pouvoir être connectée à une GPIO.

Exemple :

```text
GPIO 2 ─── Résistance ─── LED ─── GND
```

Lorsque le programme exécute :

```python
led.value(1)
```

la LED doit s'allumer.

Lorsque :

```python
led.value(0)
```

elle doit s'éteindre.

---

# 12. Simulation des boutons

Le bouton doit pouvoir être utilisé comme entrée.

Exemple :

```python
button = Pin(4, Pin.IN)
```

L'utilisateur doit pouvoir cliquer sur le bouton virtuel.

Le simulateur doit alors modifier l'état logique :

```text
NON APPUYÉ → 0
APPUYÉ     → 1
```

selon la configuration choisie.

---

# 13. Résistances

Les résistances doivent pouvoir être ajoutées au montage.

Propriétés :

- valeur ;
- unité ;
- bornes ;
- connexion ;
- orientation.

Exemples :

- 220 Ω ;
- 330 Ω ;
- 1 kΩ ;
- 10 kΩ.

---

# 14. Potentiomètre

Le potentiomètre doit être représenté graphiquement et manipulable avec la souris.

Le code :

```python
adc = ADC(Pin(34))
value = adc.read()
```

doit récupérer une valeur dépendant de la position du potentiomètre.

---

# 15. ADC

Le simulateur doit reproduire une entrée analogique.

La valeur doit pouvoir être représentée :

```text
0 → minimum
...
4095 → maximum
```

selon la configuration de l'ESP32 simulée.

---

# 16. PWM

Support de :

```python
PWM()
```

Exemple :

```python
from machine import Pin, PWM

pwm = PWM(Pin(2))
pwm.freq(1000)
pwm.duty(512)
```

La simulation doit permettre de visualiser :

- fréquence ;
- rapport cyclique ;
- niveau de sortie.

---

# 17. Servo moteur

Le servo doit pouvoir être piloté par PWM.

L'utilisateur doit pouvoir voir :

```text
0° ───────── 90° ───────── 180°
```

L'angle doit évoluer selon le programme.

---

# 18. Buzzer

Le buzzer virtuel doit réagir à :

- fréquence ;
- activation ;
- désactivation ;
- PWM.

Une représentation visuelle peut être utilisée lorsque le son n'est pas disponible.

---

# 19. Capteurs

Le système doit permettre d'ajouter des capteurs virtuels.

Chaque capteur doit disposer d'un panneau permettant de modifier ses valeurs.

Exemple :

### Température

```text
Température : 25 °C
[──────●────────]
```

Le programme récupère cette valeur.

---

# 20. Capteur ultrason

Support d'un capteur de type HC-SR04 ou équivalent.

Paramètres :

- distance ;
- trigger ;
- echo.

Exemple :

```python
trigger = Pin(5, Pin.OUT)
echo = Pin(18, Pin.IN)
```

---

# 21. DHT

Support d'un capteur température/humidité.

Valeurs simulables :

```text
Température : 24.5 °C
Humidité    : 58 %
```

---

# 22. LDR

Simulation d'un capteur de luminosité.

L'utilisateur peut modifier :

```text
Obscurité ───────────── Lumière
```

Le résultat doit modifier la valeur ADC.

---

# 23. Écrans

Le système doit pouvoir simuler :

- LCD 16x2 ;
- LCD 20x4 ;
- OLED SSD1306 ;
- écran TFT.

Exemple :

```python
display.text("Bonjour", 0, 0)
```

Le texte doit apparaître dans l'écran virtuel.

---

# 24. Bus I2C

Le simulateur devra prendre en charge progressivement :

```python
I2C()
```

avec :

- SDA ;
- SCL ;
- adresse ;
- périphériques.

Exemple :

```text
ESP32
GPIO 21 ───── SDA ───── OLED
GPIO 22 ───── SCL ───── OLED
```

---

# 25. UART

Support de la communication série.

L'application doit afficher :

```text
UART / Serial Monitor

> Démarrage...
> Température: 25.3
> LED ON
> LED OFF
```

---

# 26. Console série

La console série doit permettre :

- affichage des messages ;
- effacement ;
- défilement automatique ;
- choix du débit ;
- recherche ;
- export éventuel.

Débits courants :

```text
9600
19200
38400
57600
115200
```

---

# 27. REPL MicroPython

L'application doit intégrer un terminal REPL.

Exemple :

```text
MicroPython ESP32

>>>
>>> from machine import Pin
>>> led = Pin(2, Pin.OUT)
>>> led.value(1)
>>>
```

L'utilisateur peut exécuter des commandes directement.

---

# 28. Boutons principaux

L'interface doit proposer clairement :

### ▶ Simuler

Lance le programme dans l'environnement virtuel.

### ⏹ Stop

Arrête la simulation.

### ↻ Reset

Réinitialise la carte virtuelle.

### ✓ Vérifier

Analyse le programme.

### ⬆ Téléverser

Envoie le programme vers la carte physique.

### 🔌 Connecter

Établit la connexion avec l'ESP32.

---

# 29. Connexion à une ESP32 physique

L'application doit pouvoir détecter les cartes connectées par USB.

Informations affichées :

```text
Carte détectée

ESP32
Port : COM4
Connexion : USB
État : Connectée
```

Sur Linux :

```text
/dev/ttyUSB0
/dev/ttyACM0
```

Sur Windows :

```text
COM3
COM4
COM5
```

---

# 30. Gestion du firmware MicroPython

L'application devra prévoir une procédure permettant :

- détecter le firmware présent ;
- identifier éventuellement la version ;
- installer MicroPython ;
- mettre à jour MicroPython ;
- restaurer une installation.

Le système doit clairement distinguer :

```text
ESP32 détectée
```

et :

```text
ESP32 compatible mais MicroPython non installé
```

---

# 31. Téléversement du programme

Le bouton :

**Téléverser vers ESP32**

doit déclencher :

```text
1. Vérification du code
2. Vérification de la connexion
3. Détection de la carte
4. Préparation des fichiers
5. Transfert
6. Vérification
7. Redémarrage éventuel
8. Ouverture du terminal
```

Une barre de progression doit être affichée.

---

# 32. Gestion de main.py

Le système doit pouvoir envoyer :

```text
main.py
```

sur la carte.

Le programme peut également envoyer :

```text
boot.py
lib/
config.py
```

selon le projet.

---

# 33. Synchronisation simulation / matériel

Principe fondamental du projet :

> Le programme testé dans le simulateur doit être celui envoyé vers l'ESP32 réelle.

Le workflow sera :

```text
             ┌──────────────┐
             │  main.py     │
             └──────┬───────┘
                    │
           ┌────────┴────────┐
           │                 │
           ▼                 ▼
     Simulation          ESP32 réelle
           │                 │
           ▼                 ▼
       Résultat          Résultat
```

---

# 34. Gestion des incompatibilités

Le simulateur doit signaler lorsqu'une fonction n'est pas supportée.

Exemple :

```text
⚠ Fonction non disponible dans le simulateur

machine.WLAN

Cette fonction nécessite une ESP32 réelle.
```

Le programme peut alors être :

- simulé partiellement ;
- ou marqué comme nécessitant le matériel réel.

---

# 35. Wi-Fi

Dans une version avancée, le système devra permettre de simuler :

```python
import network
```

avec une représentation :

```text
Wi-Fi

SSID : ESP32_LAB
État : Connecté
IP : 192.168.1.20
```

La simulation devra clairement distinguer les fonctions réellement simulées des fonctions nécessitant Internet.

---

# 36. MQTT

Version avancée :

- broker MQTT ;
- topic ;
- publish ;
- subscribe ;
- messages.

Exemple :

```text
Topic:
esp32/temperature

Message:
25.4
```

---

# 37. Gestion des projets

Chaque projet doit contenir :

```text
Projet
├── Informations
├── Code
├── Schéma
├── Composants
├── Configuration
└── Historique
```

Informations :

- nom ;
- description ;
- auteur ;
- date ;
- niveau ;
- catégorie.

---

# 38. Sauvegarde

L'utilisateur doit pouvoir :

- sauvegarder ;
- ouvrir ;
- dupliquer ;
- exporter ;
- importer.

Format recommandé :

```text
.esp32lab
```

Le fichier peut contenir :

```json
{
  "name": "LED Blink",
  "board": "ESP32",
  "files": {},
  "components": [],
  "connections": []
}
```

---

# 39. Bibliothèque de projets

L'application doit proposer :

### Mes projets

```text
LED Blink
Capteur température
Servo
OLED
Station météo
```

### Exemples

- Blink ;
- Button ;
- ADC ;
- PWM ;
- Servo ;
- OLED ;
- DHT ;
- Wi-Fi ;
- MQTT.

---

# 40. Mode enseignant

L'enseignant doit pouvoir créer un exercice.

Exemple :

### Exercice

**Titre :** Commander une LED

**Objectif :**

Programmer une LED connectée au GPIO 2.

**Consigne :**

La LED doit s'allumer pendant une seconde puis s'éteindre pendant une seconde.

**Composants disponibles :**

- ESP32 ;
- LED ;
- résistance.

---

# 41. Évaluation automatique

Le système doit pouvoir vérifier :

- présence de certaines fonctions ;
- état d'une GPIO ;
- fréquence ;
- valeur analogique ;
- comportement d'un composant ;
- résultat final.

Exemple :

```text
Tests

✓ GPIO 2 configuré en sortie
✓ LED allumée
✓ LED éteinte
✓ délai respecté

Score : 100 %
```

---

# 42. Système de cours

Les cours peuvent être structurés :

```text
Cours
│
├── 01 Introduction ESP32
├── 02 Python
├── 03 MicroPython
├── 04 GPIO
├── 05 Boutons
├── 06 ADC
├── 07 PWM
├── 08 Capteurs
├── 09 Affichage
├── 10 Wi-Fi
└── 11 IoT
```

Chaque cours peut contenir :

- explication ;
- code ;
- simulation ;
- exercice ;
- correction.

---

# 43. Mode débutant

Un mode simplifié doit masquer les fonctionnalités avancées.

Exemple :

```text
Débutant

Code
Composants
Simulation
Résultat
```

Le mode avancé ajoute :

- REPL ;
- fichiers ;
- configuration ;
- ports ;
- firmware ;
- paramètres avancés.

---

# 44. Interface de simulation

Le simulateur doit permettre :

- déplacement des composants ;
- rotation ;
- suppression ;
- duplication ;
- connexion par fils ;
- modification des valeurs ;
- zoom ;
- déplacement de la vue ;
- reset du montage.

Les connexions doivent être représentées graphiquement.

---

# 45. Système de câblage

L'utilisateur doit pouvoir sélectionner :

```text
GPIO
GND
3V3
VIN
SDA
SCL
TX
RX
```

et créer une connexion.

Le système doit empêcher ou signaler certaines connexions invalides.

Exemple :

```text
⚠ Court-circuit potentiel

3V3 connecté directement à GND.
```

---

# 46. Validation électronique

Le simulateur doit pouvoir détecter progressivement :

- court-circuit ;
- alimentation incorrecte ;
- GPIO incompatible ;
- composant non alimenté ;
- absence de GND ;
- mauvaise connexion.

L'objectif n'est pas de remplacer un simulateur électronique professionnel, mais d'éviter les erreurs pédagogiques courantes.

---

# 47. Architecture technique

Architecture recommandée :

```text
┌──────────────────────────────────────┐
│              FRONTEND                │
│                                      │
│  UI + Editor + Simulator + Projects  │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│          SIMULATION ENGINE            │
│                                      │
│ GPIO / ADC / PWM / I2C / UART / etc. │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│        MICROPYTHON EXECUTION         │
│              LAYER                   │
└──────────────────┬───────────────────┘
                   │
            ┌──────┴───────┐
            ▼              ▼
       Simulation      Hardware
                         Bridge
                           │
                           ▼
                         USB
                           │
                           ▼
                         ESP32
```

---

# 48. Architecture logicielle

Le système devra séparer clairement :

## UI

Gestion de :

- fenêtres ;
- boutons ;
- menus ;
- éditeur ;
- panneaux.

## Simulation Engine

Gestion de :

- GPIO ;
- composants ;
- connexions ;
- événements ;
- horloge virtuelle.

## MicroPython Runtime

Interprétation/exécution du programme dans le contexte du simulateur.

## Hardware Manager

Gestion de :

- ports série ;
- détection ESP32 ;
- communication ;
- transfert de fichiers ;
- REPL.

## Project Manager

Gestion de :

- projets ;
- fichiers ;
- schémas ;
- sauvegarde.

---

# 49. Technologies possibles

Une architecture Desktop est recommandée pour la première version car l'accès USB est beaucoup plus simple.

### Option recommandée

**Tauri + interface Web + moteur local**

ou :

**Electron + interface Web + service local**

L'interface peut être développée avec :

- HTML/CSS/JavaScript ;
- TypeScript ;
- React éventuellement.

Le moteur de communication matériel peut être développé dans un langage adapté au système cible.

---

# 50. Pourquoi une application Desktop

Une application Desktop permet plus facilement :

- accès USB ;
- ports COM ;
- installation de firmware ;
- communication série ;
- REPL ;
- fichiers locaux.

Une version Web peut être envisagée ultérieurement.

---

# 51. Compatibilité

## Systèmes

Version initiale :

- Windows 10/11.

Version ultérieure :

- Linux ;
- macOS.

## Matériel

Priorité :

- ESP32 DevKit ;
- ESP32-WROOM.

Puis :

- ESP32-S3 ;
- ESP32-C3 ;
- ESP32-C6.

---

# 52. Gestion des cartes

L'utilisateur doit choisir :

```text
Carte

○ ESP32
○ ESP32-S3
○ ESP32-C3
○ ESP32-C6
```

Chaque carte possède sa configuration :

- GPIO ;
- ADC ;
- PWM ;
- mémoire ;
- périphériques ;
- caractéristiques spécifiques.

---

# 53. Système de plugins

À terme, l'application devra pouvoir ajouter de nouveaux composants sans modifier le cœur.

Exemple :

```text
components/
├── led/
├── button/
├── servo/
├── dht22/
├── oled/
└── hcsr04/
```

Chaque composant définit :

- représentation graphique ;
- broches ;
- propriétés ;
- comportement ;
- interface MicroPython ;
- règles de simulation.

---

# 54. Exemple de définition d'un composant

Conceptuellement :

```json
{
  "id": "led",
  "name": "LED",
  "pins": ["A", "K"],
  "properties": {
    "color": "red"
  },
  "simulation": {
    "digital_input": true
  }
}
```

---

# 55. Gestion des erreurs

Toutes les erreurs doivent être compréhensibles.

Exemples :

```text
❌ ESP32 non détectée

Vérifiez :
• le câble USB
• la connexion
• le pilote USB
```

ou :

```text
❌ Erreur MicroPython

Ligne 8 :
NameError: name 'led' isn't defined
```

---

# 56. Journal système

Un panneau de diagnostic peut afficher :

```text
[INFO] ESP32 détectée
[INFO] Port COM4
[INFO] Connexion établie
[INFO] Envoi main.py
[INFO] Transfert terminé
[INFO] Redémarrage ESP32
```

Ce mode pourra être activé dans les paramètres avancés.

---

# 57. Sécurité

Le système doit isoler le code exécuté dans le simulateur autant que possible.

Le code utilisateur ne doit pas avoir accès librement :

- au système de fichiers de l'ordinateur ;
- aux commandes système ;
- au réseau local ;

sans autorisation explicite.

Le moteur de simulation doit fonctionner dans un environnement contrôlé.

---

# 58. Performance

Le simulateur doit rester fluide avec :

- au moins 20 composants simples ;
- plusieurs GPIO ;
- plusieurs capteurs ;
- console série active.

La simulation doit pouvoir être arrêtée à tout moment.

---

# 59. Ergonomie

L'interface doit respecter :

- hiérarchie visuelle claire ;
- boutons suffisamment grands ;
- raccourcis clavier ;
- mode sombre ;
- mode clair ;
- messages d'erreur lisibles ;
- interface responsive lorsque possible.

---

# 60. Internationalisation

La première langue peut être :

**Français**

L'architecture doit cependant permettre :

- Français ;
- Anglais ;
- Arabe.

Les textes de l'interface ne doivent donc pas être codés directement dans les composants.

---

# 61. Accessibilité

Prévoir :

- contraste suffisant ;
- navigation clavier ;
- labels explicites ;
- taille de texte configurable ;
- indications visuelles et textuelles ;
- couleurs non utilisées comme seul moyen d'information.

---

# 62. MVP — Version 1

La première version doit rester volontairement limitée.

### Fonctionnalités obligatoires

**Éditeur :**

- MicroPython ;
- `main.py` ;
- coloration syntaxique ;
- sauvegarde.

**Simulation :**

- ESP32 ;
- GPIO ;
- LED ;
- bouton ;
- résistance ;
- simulation `Pin`.

**Console :**

- affichage des `print()` ;
- arrêt ;
- reset.

**Projet :**

- nouveau projet ;
- sauvegarder ;
- ouvrir.

**Hardware :**

- détection port série ;
- connexion ESP32 ;
- transfert de `main.py`.

---

# 63. Version 2

Ajouter :

- potentiomètre ;
- ADC ;
- PWM ;
- servo ;
- buzzer ;
- DHT ;
- LDR ;
- HC-SR04 ;
- OLED ;
- I2C ;
- gestion de plusieurs fichiers ;
- REPL.

---

# 64. Version 3

Ajouter :

- Wi-Fi ;
- MQTT ;
- SPI ;
- SD ;
- TFT ;
- davantage de cartes ESP32 ;
- bibliothèque de composants ;
- système de plugins.

---

# 65. Version pédagogique avancée

Ajouter :

- comptes utilisateurs ;
- classes ;
- enseignants ;
- exercices ;
- correction automatique ;
- notation ;
- progression ;
- certificats ;
- statistiques.

---

# 66. Exemple de scénario utilisateur

## Scénario 1 — Premier programme

L'élève ouvre l'application.

Il choisit :

**Nouveau projet → ESP32 → MicroPython**

L'application affiche :

```text
ESP32
+
LED GPIO 2
```

L'élève écrit :

```python
from machine import Pin
from time import sleep

led = Pin(2, Pin.OUT)

while True:
    led.value(1)
    sleep(1)
    led.value(0)
    sleep(1)
```

Il clique :

**Simuler**

La LED virtuelle clignote.

La console affiche :

```text
Simulation démarrée
LED ON
LED OFF
LED ON
LED OFF
```

L'élève connecte ensuite son ESP32.

L'application détecte :

```text
ESP32 détectée — COM4
```

Il clique :

**Téléverser vers ESP32**

Le programme est envoyé.

---

# 67. Scénario 2 — Bouton

Le montage contient :

```text
GPIO 4 → Bouton
GPIO 2 → LED
```

Code :

```python
from machine import Pin

led = Pin(2, Pin.OUT)
button = Pin(4, Pin.IN)

while True:
    led.value(button.value())
```

Dans le simulateur, l'utilisateur clique sur le bouton.

La LED s'allume.

Lorsqu'il relâche :

```text
LED OFF
```

---

# 68. Scénario 3 — Capteur

Montage :

```text
ESP32
 │
 └── DHT22
```

Code :

```python
from machine import Pin
from dht import DHT22

sensor = DHT22(Pin(4))

sensor.measure()

print(sensor.temperature())
print(sensor.humidity())
```

Le simulateur permet de modifier :

```text
Température : 28 °C
Humidité : 65 %
```

et le programme récupère ces valeurs.

---

# 69. Critères de réussite du MVP

Le MVP sera considéré comme fonctionnel lorsque l'utilisateur pourra :

1. créer un projet ;
2. sélectionner ESP32 ;
3. écrire du MicroPython ;
4. placer une LED ;
5. connecter la LED à GPIO 2 ;
6. exécuter le programme ;
7. voir la LED réagir ;
8. afficher les `print()` ;
9. arrêter la simulation ;
10. connecter une ESP32 physique ;
11. détecter son port ;
12. envoyer `main.py` ;
13. ouvrir le REPL ;
14. observer les messages série.

---

# 70. Tests fonctionnels

Chaque fonctionnalité devra disposer de tests.

Exemple :

### Test GPIO

```text
Créer Pin(2, OUT)
→ OK

digitalWrite(2, 1)
→ LED ON

digitalWrite(2, 0)
→ LED OFF
```

### Test matériel

```text
Brancher ESP32
→ Port détecté

Téléverser main.py
→ Fichier transféré

Redémarrer
→ main.py exécuté
```

---

# 71. Tests de robustesse

Tester :

- ESP32 débranchée pendant transfert ;
- mauvais port ;
- câble défectueux ;
- code invalide ;
- fichier absent ;
- simulation infinie ;
- mémoire insuffisante ;
- composant non connecté ;
- GPIO inexistante ;
- mauvais type de carte.

---

# 72. Documentation

La plateforme doit disposer d'une documentation intégrée.

Sections :

```text
Démarrage
MicroPython
ESP32
GPIO
ADC
PWM
I2C
SPI
UART
Capteurs
Affichage
Wi-Fi
Projets
Téléversement
Dépannage
```

---

# 73. Aide contextuelle

Lorsque l'utilisateur sélectionne :

```python
Pin()
```

l'application peut afficher :

```text
Pin()

Permet de contrôler une broche GPIO
de l'ESP32.

Exemple :
Pin(2, Pin.OUT)
```

---

# 74. Architecture de données

Les données principales seront :

```text
User
Project
ProjectFile
Board
Component
Connection
Simulation
Exercise
Course
Submission
Result
```

Relations principales :

```text
User
 │
 ├── Projects
 │      ├── Files
 │      ├── Components
 │      └── Connections
 │
 └── Submissions
```

---

# 75. Évolutivité

Le système doit être conçu pour permettre ultérieurement :

- Raspberry Pi Pico ;
- Arduino ;
- autres microcontrôleurs ;
- ESP8266 ;
- nouveaux langages ;
- nouveaux composants ;
- nouvelles plateformes pédagogiques.

L'ESP32/MicroPython reste toutefois le cœur de la première version.

---

# 76. Architecture cible finale

```text
                     ESP32 MICRO PYTHON LAB
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       PROGRAMMER          SIMULER            EXPÉRIMENTER
          │                   │                   │
       Python             ESP32 virtuelle       ESP32 réelle
          │                   │                   │
       Éditeur             GPIO                 USB
       Debug               ADC                  REPL
       Fichiers            PWM                  Serial
          │                I2C                  Upload
          │                SPI
          │                   │
          └───────────────────┼───────────────────┘
                              │
                         APPRENDRE
                              │
                   ┌──────────┼──────────┐
                   │          │          │
                 Cours     Exercices   Évaluation
```

---

# 77. Priorités de développement

## Priorité P0 — indispensable

- interface ;
- éditeur MicroPython ;
- ESP32 virtuelle ;
- GPIO ;
- LED ;
- bouton ;
- simulation ;
- console ;
- projets ;
- USB ;
- téléversement.

## Priorité P1 — importante

- ADC ;
- PWM ;
- potentiomètre ;
- servo ;
- OLED ;
- DHT ;
- I2C ;
- REPL ;
- plusieurs fichiers.

## Priorité P2 — avancée

- Wi-Fi ;
- MQTT ;
- SPI ;
- SD ;
- TFT ;
- système de plugins.

## Priorité P3 — pédagogique

- comptes ;
- classes ;
- cours ;
- exercices ;
- correction automatique ;
- statistiques ;
- espace enseignant.

---

# 78. Résultat attendu

À terme, l'application doit devenir un véritable :

## « laboratoire ESP32 MicroPython »

dans lequel un utilisateur peut :

**apprendre → programmer → câbler → simuler → corriger → tester → téléverser → mesurer**

dans une seule application.

La caractéristique différenciante du projet sera la continuité entre le **montage virtuel et le montage réel** : le même projet, le même code et la même logique pourront passer du simulateur à l'ESP32 physique.

---

# 79. Livrables

Le projet devra produire :

### Logiciel

- application Desktop ;
- moteur de simulation ;
- module MicroPython ;
- gestionnaire ESP32 ;
- gestionnaire de projets.

### Bibliothèque

- composants virtuels ;
- modèles ESP32 ;
- exemples MicroPython.

### Documentation

- manuel utilisateur ;
- documentation technique ;
- documentation développeur ;
- guide enseignant.

### Tests

- tests unitaires ;
- tests d'intégration ;
- tests hardware ;
- tests de simulation.

---

# 80. Conclusion

Le projet ne doit pas être conçu comme un simple éditeur de code ou un simple simulateur.

Il doit être conçu comme une **plateforme intégrée d'apprentissage et d'expérimentation ESP32/MicroPython**.

L'architecture doit donc dès le départ séparer :

**Interface / Éditeur / Runtime MicroPython / Simulateur / Matériel / Pédagogie.**

Cette séparation permettra de commencer avec un MVP relativement simple — **ESP32 + LED + GPIO + MicroPython** — tout en conservant une architecture capable d'évoluer vers un véritable environnement de laboratoire IoT.

**MVP recommandé :**

> `ESP32 + MicroPython + éditeur + simulateur + LED + bouton + console + USB + téléversement`

puis extension progressive vers les capteurs, écrans, communications et fonctionnalités pédagogiques.