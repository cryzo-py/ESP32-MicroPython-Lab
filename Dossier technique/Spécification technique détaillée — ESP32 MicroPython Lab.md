# Spécification technique détaillée

## ESP32 MicroPython Lab

**Version :** 1.0  
**Statut :** Spécification technique  
**Type :** Application Desktop éducative  
**Langage principal :** Python 3.12+  
**Framework GUI :** PySide6 / Qt 6  
**Cible principale :** Windows 10/11  
**Carte cible :** ESP32  
**Langage embarqué :** MicroPython

---

# 1. Objet du document

Ce document définit l'architecture technique, les composants logiciels, les interfaces, les modèles de données et les exigences de développement de l'application **ESP32 MicroPython Lab**.

L'application a pour objectif de fournir un environnement intégré permettant de :

- programmer une ESP32 avec MicroPython ;
- concevoir un circuit électronique virtuel ;
- simuler son fonctionnement ;
- visualiser les entrées et sorties ;
- consulter les résultats ;
- communiquer avec une ESP32 physique ;
- transférer des programmes ;
- utiliser le REPL MicroPython ;
- gérer des projets ;
- proposer ultérieurement des cours et exercices.

---

# 2. Vision technique

L'application doit permettre le passage suivant :

```text
Code MicroPython
       │
       ▼
Validation
       │
       ▼
Simulation virtuelle
       │
       ▼
Correction
       │
       ▼
ESP32 physique
       │
       ▼
Téléversement
       │
       ▼
Exécution réelle
```

Le principe fondamental est que le même projet doit pouvoir être utilisé dans le simulateur puis sur une ESP32 physique.

---

# 3. Principes architecturaux

Le développement doit respecter les principes suivants :

1. séparation de l'interface et de la logique métier ;
2. séparation du simulateur et du matériel réel ;
3. architecture modulaire ;
4. composants électroniques extensibles ;
5. faible couplage entre modules ;
6. code testable ;
7. sécurité du code utilisateur ;
8. possibilité d'ajouter de nouvelles cartes ;
9. possibilité d'ajouter de nouveaux composants ;
10. possibilité d'ajouter une plateforme pédagogique.

---

# 4. Stack technologique

## 4.1. Langage

```text
Python 3.12+
```

Python est utilisé pour :

- interface ;
- moteur de simulation ;
- gestion des projets ;
- communication série ;
- logique pédagogique ;
- tests.

---

# 5. Interface graphique

## 5.1. PySide6

Framework principal :

```text
PySide6
```

Composants Qt utilisés :

- `QMainWindow`
- `QWidget`
- `QDockWidget`
- `QSplitter`
- `QTabWidget`
- `QTreeView`
- `QListView`
- `QGraphicsView`
- `QGraphicsScene`
- `QTextEdit`
- `QDialog`
- `QMenu`
- `QToolBar`
- `QStatusBar`

---

# 6. Éditeur de code

Technologie recommandée :

```text
QScintilla
```

Fonctionnalités :

- syntax highlighting Python ;
- numérotation des lignes ;
- indentation ;
- folding ;
- recherche ;
- remplacement ;
- sélection multiple ;
- markers ;
- affichage des erreurs ;
- autocomplétion ;
- sauvegarde.

---

# 7. Communication avec ESP32

Bibliothèque :

```text
pyserial
```

Fonctions :

- détection des ports ;
- ouverture du port ;
- fermeture ;
- lecture ;
- écriture ;
- configuration baudrate ;
- communication REPL ;
- transfert de données.

---

# 8. Base de données

Technologie :

```text
SQLite
```

SQLite sera utilisée pour :

- paramètres ;
- projets ;
- exercices ;
- cours ;
- utilisateurs locaux ;
- historique.

Pour le MVP, aucune base de données distante n'est obligatoire.

---

# 9. Stockage des projets

Format principal :

```text
.esp32lab
```

Un projet doit être portable.

Structure conceptuelle :

```text
MyProject.esp32lab
│
├── project.json
├── circuit.json
├── main.py
├── boot.py
├── config.py
└── assets/
```

---

# 10. Architecture générale

```text
┌────────────────────────────────────────────────────────────┐
│                       PySide6 UI                           │
│                                                            │
│ Editor │ Circuit │ Simulator │ Console │ Projects │ Cours │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                    Application Core                        │
│                                                            │
│ Project │ Simulation │ Components │ Board │ Exercises     │
└──────────────────────────┬─────────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
┌──────────────────────────┐   ┌────────────────────────────┐
│   MicroPython Runtime    │   │      Hardware Manager      │
│                          │   │                            │
│ Pin / ADC / PWM / I2C    │   │ Serial / REPL / Upload     │
│ UART / Time / Network    │   │ Firmware / Detection       │
└────────────┬─────────────┘   └──────────────┬─────────────┘
             │                                │
             ▼                                ▼
      Virtual ESP32                    Physical ESP32
```

---

# 11. Architecture des packages

```text
esp32_lab/
│
├── main.py
│
├── app/
│   ├── application.py
│   ├── configuration.py
│   └── theme.py
│
├── ui/
│   ├── main_window.py
│   │
│   ├── editor/
│   │   ├── code_editor.py
│   │   ├── editor_manager.py
│   │   └── syntax.py
│   │
│   ├── simulator/
│   │   ├── simulator_view.py
│   │   ├── board_view.py
│   │   ├── wire_view.py
│   │   └── scene.py
│   │
│   ├── components/
│   │   ├── library_widget.py
│   │   └── properties_widget.py
│   │
│   ├── console/
│   │   ├── console_widget.py
│   │   └── repl_widget.py
│   │
│   └── dialogs/
│
├── core/
│   ├── project/
│   ├── simulation/
│   ├── micropython/
│   ├── boards/
│   ├── components/
│   └── exercises/
│
├── hardware/
│   ├── serial_manager.py
│   ├── esp32_manager.py
│   ├── firmware_manager.py
│   ├── uploader.py
│   └── repl.py
│
├── simulator/
│   ├── engine.py
│   ├── clock.py
│   ├── gpio.py
│   ├── adc.py
│   ├── pwm.py
│   ├── i2c.py
│   ├── spi.py
│   ├── uart.py
│   └── runtime.py
│
├── components/
│   ├── base.py
│   ├── led.py
│   ├── button.py
│   ├── resistor.py
│   ├── potentiometer.py
│   ├── buzzer.py
│   ├── servo.py
│   ├── dht11.py
│   ├── dht22.py
│   ├── hcsr04.py
│   ├── oled.py
│   └── lcd.py
│
├── models/
│   ├── project.py
│   ├── board.py
│   ├── component.py
│   ├── connection.py
│   └── exercise.py
│
├── database/
│   ├── database.py
│   ├── migrations.py
│   └── repositories/
│
├── services/
│   ├── project_service.py
│   ├── simulation_service.py
│   └── hardware_service.py
│
├── tests/
│
└── resources/
    ├── icons/
    ├── boards/
    └── components/
```

---

# 12. Modèle MVC / MVVM

L'application doit séparer :

```text
Model
View
ViewModel / Controller
```

Exemple :

```text
Project
   │
   ▼
ProjectService
   │
   ▼
MainWindow
```

La fenêtre ne doit pas directement modifier la base de données.

---

# 13. Modèle Project

```python
@dataclass
class Project:
    id: str
    name: str
    description: str
    board: str
    files: list
    components: list
    connections: list
    created_at: str
    updated_at: str
```

---

# 14. Modèle Board

```python
@dataclass
class Board:
    id: str
    name: str
    model: str
    pins: list
    capabilities: dict
```

Exemple :

```text
ESP32
ESP32-S3
ESP32-C3
ESP32-C6
```

---

# 15. Modèle Pin

```python
@dataclass
class Pin:
    number: int
    name: str
    input_supported: bool
    output_supported: bool
    adc_supported: bool
    pwm_supported: bool
```

---

# 16. Modèle Component

```python
@dataclass
class Component:
    id: str
    type: str
    x: float
    y: float
    rotation: float
    properties: dict
    pins: list
```

---

# 17. Modèle Connection

```python
@dataclass
class Connection:
    id: str

    from_component: str
    from_pin: str

    to_component: str
    to_pin: str
```

---

# 18. Circuit Designer

Le circuit sera basé sur :

```text
QGraphicsScene
        │
        ├── ESP32
        ├── LED
        ├── Button
        ├── Resistor
        └── Wires
```

Chaque élément graphique sera un `QGraphicsItem`.

---

# 19. Classe graphique de base

```python
class ComponentGraphicsItem(QGraphicsItem):
    component: Component
```

Responsabilités :

- affichage ;
- déplacement ;
- sélection ;
- rotation ;
- interaction.

La logique électronique ne doit pas être contenue dans cette classe.

---

# 20. Architecture d'un composant

Chaque composant sera divisé en trois parties :

```text
LED
│
├── model
├── graphics
└── runtime
```

Exemple :

```text
led.py
led_graphics.py
led_runtime.py
```

---

# 21. Simulation Engine

Classe principale :

```python
class SimulationEngine:
    def start(self): ...
    def pause(self): ...
    def stop(self): ...
    def reset(self): ...
```

Elle possède :

```text
VirtualBoard
GPIOManager
ADCManager
PWMManager
I2CManager
UARTManager
SimulationClock
MicroPythonRuntime
```

---

# 22. Simulation Context

```python
@dataclass
class SimulationContext:
    board: Board
    gpio: object
    adc: object
    pwm: object
    i2c: object
    uart: object
    clock: object
```

Chaque composant reçoit ce contexte.

---

# 23. Virtual ESP32

```python
class VirtualESP32:
    def __init__(self, board):
        self.board = board
        self.gpio = GPIOManager()
        self.adc = ADCManager()
        self.pwm = PWMManager()
        self.i2c = I2CBus()
        self.uart = UARTManager()
```

---

# 24. GPIO Manager

```python
class GPIOManager:
    def configure(self, pin, mode):
        ...

    def write(self, pin, value):
        ...

    def read(self, pin):
        ...
```

États :

```text
LOW
HIGH
INPUT
OUTPUT
INPUT_PULLUP
INPUT_PULLDOWN
```

---

# 25. Simulation Pin

L'API simulée doit permettre :

```python
from machine import Pin

led = Pin(2, Pin.OUT)

led.value(1)
led.value(0)
```

---

# 26. Mapping MicroPython → simulateur

```text
Pin(2, OUT)
       │
       ▼
VirtualPin(2)
       │
       ▼
GPIOManager
       │
       ▼
Circuit
       │
       ▼
LED
```

---

# 27. Simulation LED

```python
class LEDRuntime:
    def on_pin_changed(self, value):
        self.state = bool(value)
```

La vue graphique reçoit ensuite :

```text
LED_STATE_CHANGED
```

---

# 28. Simulation Button

```python
class ButtonRuntime:
    def press(self):
        ...

    def release(self):
        ...
```

Le bouton graphique déclenche :

```text
press()
```

qui modifie le GPIO correspondant.

---

# 29. Simulation ADC

```python
class ADCManager:

    def set_value(self, pin, value):
        ...

    def read(self, pin):
        ...
```

Plage initiale :

```text
0 → 4095
```

---

# 30. Potentiomètre

Le potentiomètre graphique fournit :

```text
0 → 4095
```

au `ADCManager`.

---

# 31. PWM

```python
class PWMChannel:
    frequency: int
    duty: int
```

API :

```python
pwm.freq(1000)
pwm.duty(512)
```

---

# 32. Servo

Le runtime servo convertit le signal PWM en angle.

```text
PWM
 │
 ▼
ServoRuntime
 │
 ▼
Angle 0–180°
 │
 ▼
ServoGraphics
```

---

# 33. I2C

```python
class I2CBus:

    def register_device(self, device):
        ...

    def scan(self):
        ...

    def readfrom(self, address, nbytes):
        ...

    def writeto(self, address, data):
        ...
```

---

# 34. UART

```python
class VirtualUART:

    def write(self, data):
        ...

    def read(self):
        ...
```

Les données sont redirigées vers la console.

---

# 35. Console

La console doit recevoir un flux unifié :

```text
Simulation UART
       │
       ├─────┐
Physical UART│
       │     │
       └──┬──┘
          ▼
      Console
```

Ainsi l'utilisateur retrouve la même interface dans les deux modes.

---

# 36. MicroPython Runtime

Le runtime doit fournir un environnement contrôlé permettant d'exposer :

```text
machine
time
network
dht
ssd1306
```

selon les fonctionnalités disponibles.

---

# 37. API `machine`

MVP :

```text
Pin
PWM
ADC
```

Version 2 :

```text
I2C
SPI
UART
Timer
RTC
```

---

# 38. API `time`

Support minimal :

```python
sleep()
sleep_ms()
sleep_us()
ticks_ms()
ticks_us()
```

---

# 39. Fonction `print()`

Les sorties :

```python
print("Hello")
```

doivent être envoyées vers :

```text
ConsoleWidget
```

---

# 40. Exécution non bloquante

Le code utilisateur ne doit jamais bloquer l'interface Qt.

Le runtime doit être exécuté dans :

```text
QThread
```

ou un worker dédié.

Architecture :

```text
Main Qt Thread
       │
       ├── UI
       └── Rendering

Simulation Worker
       │
       └── MicroPython Runtime
```

---

# 41. Arrêt du runtime

Le système doit permettre :

```text
Start
Pause
Resume
Stop
Reset
```

Un programme contenant :

```python
while True:
```

doit pouvoir être interrompu.

---

# 42. Validation du code

Avant exécution :

```text
Code
 ↓
Syntax validation
 ↓
Runtime validation
 ↓
Simulation
```

Les erreurs doivent être associées à une ligne.

---

# 43. Validation du circuit

Avant simulation :

```text
CircuitValidator
```

vérifie :

- GPIO ;
- connexions ;
- alimentation ;
- conflits ;
- composants incomplets.

---

# 44. Messages d'erreur

Exemple :

```text
Erreur ligne 8

NameError:
name 'led' is not defined
```

ou :

```text
GPIO Error

GPIO34 ne peut pas être utilisé
comme sortie numérique.
```

---

# 45. Hardware Manager

```python
class HardwareManager:

    def list_ports(self):
        ...

    def connect(self, port):
        ...

    def disconnect(self):
        ...

    def write(self, data):
        ...

    def read(self):
        ...
```

---

# 46. Serial Manager

```python
class SerialManager:
    port
    baudrate
    serial
```

Fonctions :

```text
open()
close()
read()
write()
flush()
```

---

# 47. Détection des ports

L'application doit détecter automatiquement les ports disponibles.

Exemple :

```text
COM3
COM4
COM7
```

L'utilisateur peut sélectionner le port manuellement.

---

# 48. Détection de la carte

Le système doit tenter d'identifier :

```text
ESP32
ESP32-S3
ESP32-C3
ESP32-C6
```

La détection doit rester configurable manuellement.

---

# 49. REPL

Le REPL physique utilise :

```text
SerialManager
      │
      ▼
REPLManager
      │
      ▼
REPLWidget
```

Le widget doit permettre :

- saisie ;
- historique ;
- copier/coller ;
- interruption ;
- reset.

---

# 50. Téléversement

Le service :

```python
class Uploader:
    def upload_project(self, project):
        ...
```

doit :

1. vérifier le projet ;
2. vérifier la connexion ;
3. préparer les fichiers ;
4. transférer ;
5. vérifier ;
6. redémarrer.

---

# 51. Upload des fichiers

Priorité :

```text
main.py
```

Puis :

```text
boot.py
lib/*
config.py
```

---

# 52. Firmware Manager

Fonctions :

```text
detect_firmware()
install_firmware()
erase_flash()
reset_device()
get_version()
```

La gestion du firmware sera séparée de l'upload des fichiers.

---

# 53. Gestion des versions MicroPython

L'application doit afficher :

```text
MicroPython
Version : x.x.x
Board : ESP32
```

et avertir lorsque le firmware est incompatible.

---

# 54. Architecture Hardware Abstraction Layer

Interface :

```python
class DeviceTarget:
    def connect(self): ...
    def disconnect(self): ...
    def reset(self): ...
    def upload(self, files): ...
```

Implémentations :

```text
VirtualESP32Target
PhysicalESP32Target
```

Cette abstraction est fondamentale.

---

# 55. Project Service

```python
class ProjectService:

    def create_project(self):
        ...

    def save_project(self, project):
        ...

    def load_project(self, path):
        ...

    def export_project(self, project):
        ...
```

---

# 56. Autosave

L'application doit sauvegarder automatiquement après une modification.

Le délai recommandé :

```text
1–2 secondes après la dernière modification.
```

---

# 57. Undo / Redo

L'éditeur utilise son propre historique.

Le circuit utilise un historique séparé.

---

# 58. Format JSON

Exemple :

```json
{
  "version": 1,
  "name": "LED Blink",
  "board": "esp32",
  "files": [
    {
      "path": "main.py",
      "content": "..."
    }
  ],
  "components": [],
  "connections": []
}
```

---

# 59. Versionnement du format

Le champ :

```json
"version": 1
```

est obligatoire.

Lors d'une évolution du format :

```text
version 1
↓
migration
↓
version 2
```

---

# 60. Base SQLite

Tables minimales :

```text
projects
project_files
courses
lessons
exercises
submissions
settings
```

---

# 61. Repository Pattern

Exemple :

```python
class ProjectRepository:

    def create(self, project):
        ...

    def get(self, project_id):
        ...

    def update(self, project):
        ...

    def delete(self, project_id):
        ...
```

Cela évite de mélanger SQL et interface graphique.

---

# 62. Bibliothèque des composants

Chaque composant doit posséder :

```text
ID
Nom
Catégorie
Icône
Modèle
Pins
Propriétés
Runtime
Graphics
```

---

# 63. Manifeste composant

Exemple :

```json
{
  "id": "led",
  "name": "LED",
  "category": "output",
  "pins": [
    {
      "id": "A",
      "type": "digital"
    },
    {
      "id": "K",
      "type": "ground"
    }
  ]
}
```

---

# 64. Plugin System

À terme, un nouveau composant pourra être ajouté sans modifier le moteur principal.

Exemple :

```text
plugins/
└── ds18b20/
    ├── manifest.json
    ├── runtime.py
    └── graphics.py
```

---

# 65. Interface graphique principale

La `MainWindow` contiendra :

```text
MenuBar
ToolBar
ProjectExplorer
ComponentLibrary
CodeEditor
SimulatorView
PropertiesPanel
Console
StatusBar
```

---

# 66. Layout

```text
┌───────────────────────────────────────────────────────┐
│ Menu / Toolbar                                        │
├──────────┬──────────────────────────┬─────────────────┤
│ Projet   │                          │ Composants      │
│ Fichiers │       Code Editor        │ / Propriétés    │
│          │                          │                 │
├──────────┼──────────────────────────┼─────────────────┤
│          │      Circuit Simulator   │                 │
│          │                          │                 │
├──────────┴──────────────────────────┴─────────────────┤
│ Console / REPL                                        │
└───────────────────────────────────────────────────────┘
```

---

# 67. Thème

Deux thèmes :

```text
Light
Dark
```

Le thème doit être centralisé dans :

```text
app/theme.py
```

---

# 68. Raccourcis clavier

Prévoir :

```text
Ctrl+N → Nouveau projet
Ctrl+O → Ouvrir
Ctrl+S → Sauvegarder
Ctrl+Z → Undo
Ctrl+Y → Redo
F5     → Simuler
F6     → Stop
F7     → Vérifier
F8     → Téléverser
```

---

# 69. Gestion des états

L'interface doit connaître :

```text
PROJECT_CLEAN
PROJECT_MODIFIED

SIMULATION_STOPPED
SIMULATION_RUNNING
SIMULATION_PAUSED

ESP32_DISCONNECTED
ESP32_CONNECTED
UPLOADING
```

---

# 70. Event Bus

Un bus d'événements interne peut être utilisé :

```text
PROJECT_CHANGED
CODE_CHANGED
COMPONENT_ADDED
WIRE_ADDED
GPIO_CHANGED
SERIAL_RECEIVED
SIMULATION_STARTED
SIMULATION_STOPPED
ESP32_CONNECTED
UPLOAD_PROGRESS
```

---

# 71. Threading

Le thread Qt principal doit rester réservé à l'interface.

Travaux en arrière-plan :

- simulation ;
- lecture série ;
- upload ;
- détection hardware ;
- opérations longues.

Utiliser :

```text
QThread
QObject Worker
Signals / Slots
```

---

# 72. Signal / Slot

Exemple :

```python
simulation_finished = Signal()
gpio_changed = Signal(int, int)
serial_received = Signal(bytes)
```

La communication entre threads doit utiliser les mécanismes Qt.

---

# 73. Journalisation

Module :

```text
logging
```

Niveaux :

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Fichier :

```text
logs/application.log
```

---

# 74. Gestion des exceptions

Les exceptions inattendues doivent être interceptées au niveau application.

L'utilisateur doit voir :

```text
Une erreur inattendue s'est produite.

Consultez les logs pour plus d'informations.
```

---

# 75. Sécurité du runtime

Le code utilisateur doit être exécuté dans un environnement contrôlé.

Interdire ou limiter :

```text
os
subprocess
socket
ctypes
pathlib vers système
```

selon le niveau de simulation.

L'objectif est d'empêcher qu'un programme pédagogique puisse exécuter arbitrairement des commandes sur l'ordinateur.

---

# 76. Limites de simulation

La simulation doit indiquer clairement :

```text
✓ Fonction simulée
⚠ Fonction partiellement simulée
● Fonction nécessitant une ESP32 réelle
```

Exemple :

```text
GPIO        ✓
ADC         ✓
PWM         ✓
I2C         ✓
Wi-Fi       ⚠
Bluetooth   ●
```

---

# 77. Tests unitaires

Framework :

```text
pytest
```

Tester :

```text
GPIOManager
ADCManager
PWMManager
ProjectService
CircuitValidator
Uploader
```

---

# 78. Tests GUI

Utiliser les outils Qt/PySide appropriés pour tester :

- création projet ;
- ajout composant ;
- simulation ;
- arrêt ;
- sauvegarde.

---

# 79. Tests Hardware

Une suite de tests avec une vraie ESP32 devra vérifier :

```text
Detection
Connection
REPL
Upload
Reset
Serial
```

---

# 80. Tests d'intégration

Test principal :

```text
Code
 ↓
MicroPython Runtime
 ↓
Pin
 ↓
GPIO
 ↓
LED
```

Puis :

```text
Code
 ↓
Uploader
 ↓
ESP32
 ↓
main.py
 ↓
GPIO
```

---

# 81. MVP — périmètre exact

La version MVP doit contenir uniquement :

## Interface

- MainWindow ;
- éditeur ;
- simulateur ;
- console ;
- bibliothèque composants.

## MicroPython

- `Pin` ;
- `sleep` ;
- `print`.

## Simulation

- ESP32 ;
- GPIO ;
- LED ;
- bouton ;
- résistance.

## Hardware

- détection COM ;
- connexion ;
- REPL ;
- upload `main.py`.

## Projet

- nouveau ;
- ouvrir ;
- sauvegarder ;
- export.

---

# 82. Version 2

Ajouter :

```text
ADC
PWM
Potentiomètre
Servo
Buzzer
DHT11
DHT22
OLED
I2C
```

---

# 83. Version 3

Ajouter :

```text
SPI
UART avancé
HC-SR04
LCD
TFT
RGB LED
Relay
Motor
Wi-Fi
MQTT
```

---

# 84. Version pédagogique

Ajouter :

```text
Utilisateurs
Classes
Cours
Leçons
Exercices
Tests
Notation
Progression
Statistiques
```

---

# 85. Roadmap de développement

## Phase 1 — Foundation

```text
PySide6
Architecture
MainWindow
Project Manager
Editor
```

## Phase 2 — Simulator

```text
QGraphicsScene
ESP32
GPIO
LED
Button
Wires
```

## Phase 3 — MicroPython

```text
Runtime
Pin
sleep
print
```

## Phase 4 — Hardware

```text
PySerial
COM detection
REPL
Upload
```

## Phase 5 — Components

```text
ADC
PWM
Servo
Sensors
OLED
```

## Phase 6 — Education

```text
Courses
Exercises
Evaluation
Students
Teachers
```

---

# 86. Critère de réussite principal

Le projet est considéré comme techniquement viable lorsque le scénario suivant fonctionne :

```text
Créer projet
      ↓
Choisir ESP32
      ↓
Ajouter LED
      ↓
Connecter GPIO2
      ↓
Écrire main.py
      ↓
Vérifier
      ↓
Simuler
      ↓
LED virtuelle clignote
      ↓
Brancher ESP32
      ↓
Détecter COM
      ↓
Téléverser main.py
      ↓
ESP32 redémarre
      ↓
LED physique clignote
```

---

# 87. Architecture finale

```text
                           PySide6
                              │
                    ┌─────────┴─────────┐
                    │                   │
                 Editor             Simulator UI
                    │                   │
                    └─────────┬─────────┘
                              │
                        Application Core
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
          Project         Simulation        Hardware
          Manager          Engine            Manager
              │               │                │
              │               ▼                ▼
              │        MicroPython        Serial / USB
              │           Runtime               │
              │               │                 │
              │               ▼                 ▼
              │         Virtual ESP32      Physical ESP32
              │
              ▼
            SQLite
```

---

# 88. Décision technique finale

La stack de référence du projet est donc :

```text
Python 3.12+
        +
PySide6 / Qt 6
        +
QScintilla
        +
PySerial
        +
SQLite
        +
Pytest
```

Le projet sera développé en privilégiant une architecture modulaire afin que le moteur de simulation, les composants, le système pédagogique et la communication avec le matériel puissent évoluer indépendamment.

Le **MVP ne cherchera pas à simuler toute l'ESP32**. Il simulera d'abord les fonctionnalités MicroPython utiles à l'apprentissage, puis étendra progressivement la couverture fonctionnelle.