# 📚 Documentation Complète : ESP32 MicroPython Lab (V1.0)

## 1. Présentation Générale
**ESP32 MicroPython Lab** est un environnement de développement, de simulation et d'apprentissage destiné à l'écosystème ESP32 sous MicroPython. Il permet de concevoir des circuits sur une breadboard virtuelle, d'écrire du code Python, et de simuler l'exécution matérielle et logicielle en temps réel, le tout sans nécessiter de composants physiques.

**Public cible :** Professeurs, étudiants, makers et développeurs IoT.

---

## 2. Architecture Globale

L'application suit un modèle MVC (Modèle-Vue-Contrôleur) fortement découplé, reposant sur des signaux asynchrones pour garantir la fluidité de l'interface (UI) pendant que le moteur physique tourne.

```mermaid
graph TD
    subgraph Frontend [Interface Utilisateur (PySide6)]
        UI_Canvas[Canvas 2D Breadboard]
        UI_Code[Éditeur de Code (QScintilla)]
        UI_Console[Console Série / Oscilloscope]
    end

    subgraph Backend [Moteur de Simulation]
        Sim_Engine[Simulation Engine]
        Net_Resolver[Résolveur Électrique (ERC)]
        Sandbox[MicroPython Runtime Thread]
        
        Mgr_GPIO[GPIO / PWM / ADC / IRQ]
        Mgr_Bus[I2C / SPI / UART]
    end

    subgraph Edu [Moteur Pédagogique]
        Eval_AST[Analyseur de Code AST]
        Eval_Topo[Évaluateur de Topologie]
    end

    UI_Canvas <-->|Topologie| Net_Resolver
    UI_Code -->|Code Source| Sandbox
    Sandbox <-->|Signaux| Sim_Engine
    Sim_Engine --> Mgr_GPIO
    Sim_Engine --> Mgr_Bus
    Net_Resolver --> Sim_Engine
    
    Eval_AST -.-> Sandbox
    Eval_Topo -.-> Net_Resolver
```

---

## 3. Le Moteur de Simulation Électrique

### 3.1 Résolveur de Nœuds (Electrical Net Resolver)
L'application ne se contente pas de relier visuellement des composants. Elle calcule les *équipotentielles* :
- Utilise un parcours de graphe (BFS) pour déterminer quels trous de la breadboard, câbles (jumpers) et broches sont connectés ensemble.
- Résout instantanément les tensions appliquées (3V3, 5V, GND).
- Détecte les anomalies matérielles avant même de lancer le code (court-circuits VCC-GND, broches flottantes).

### 3.2 Gestionnaires Périphériques (Managers)
Le `SimulationEngine` délègue les tâches à des gestionnaires ultra-spécialisés :
- **GPIO / PWM / ADC** : Traduisent les états logiques (`0`/`1`) et analogiques (0-4095) vers les composants (allumer une LED, lire un potentiomètre).
- **I2C Manager** : Gère la topologie de bus (SDA/SCL). Scanne les adresses actives (ex: `0x3C` pour l'OLED, `0x76` pour le BME280) et route les octets virtuels vers les modèles de composants via `writeto_mem`.
- **SPI / UART Managers** : Gèrent les flux de données synchrones et asynchrones pour des composants comme la mémoire Flash (W25Q) ou le moniteur série.
- **IRQ / Timers** : Gèrent les interruptions matérielles asynchrones (fronts montants/descendants sur boutons) de manière Thread-Safe.

---

## 4. L'Environnement d'Exécution (Sandbox MicroPython)

Le code écrit par l'utilisateur n'est pas exécuté directement dans le processus principal pour des raisons de sécurité et de stabilité.
- **Isolation (Thread Worker)** : Le code tourne dans un thread séparé. Une boucle infinie (`while True: pass`) ne gèle jamais l'interface utilisateur.
- **Surcharge des Modules** : Les bibliothèques standard de MicroPython sont interceptées et remplacées par des versions simulées :
  - `machine.Pin`, `machine.PWM`, `machine.ADC`, `machine.I2C`, `machine.SPI` : Communiquent avec le `SimulationEngine`.
  - `time.sleep`, `time.ticks_ms` : Synchronisés avec le temps virtuel de la simulation.
  - `network`, `mqtt` : Émulent des connexions WiFi et des requêtes réseau.

---

## 5. Composants Matériels Virtuels Pris en Charge

| Catégorie | Composants inclus | Fonctionnalités de Simulation |
| :--- | :--- | :--- |
| **Cœur** | ESP32-WROOM-32 | 34 GPIOs, WiFi émulé, 3V3/GND/5V. |
| **Passifs** | Résistance, Câbles Dupont | Routage électrique sur Breadboard. |
| **I/O Basiques**| LED (Rouge, Verte, Bleue...), Bouton Poussoir, Switch | Interactions cliquables, PWM pour la luminosité LED. |
| **Analogique** | Potentiomètre rotatif | Rotation UI à la souris, conversion ADC 12 bits (0-4095). |
| **Actuateurs** | Servomoteur (SG90) | Réagit aux signaux PWM (rapport cyclique), rotation du bras animée. |
| **I2C / SPI** | Écran OLED (SSD1306), Capteur BME280 (Temp/Hum) | Algorithme de rendu pixels, tampons (framebuffers), courbes météo dynamiques. |

---

## 6. Moteur Pédagogique (TP et Exercices)

Le module d'apprentissage assiste l'étudiant à travers des JSON de scénarisation.
- **Analyse Statique (AST)** : Vérifie sans exécuter le code si l'étudiant a utilisé les bonnes classes (`Pin.IN`, `PWM`, boucle `while`).
- **Analyse Topologique** : Vérifie que le câblage de l'étudiant correspond aux attentes (ex: LED sur le GPIO 4 reliée à une résistance de 220Ω).
- **Système de "Hints" (Indices)** : Fournit un retour visuel précis et non punitif en cas d'erreur (ex: *"Attention, tu as branché la LED à l'envers (Anode sur le GND)."*).

---

## 7. Structure de l'Arborescence du Code

```text
esp32_lab/
├── core/                   # Logique métier, modèles de données, Résolveur (ERC)
│   ├── models/             # Classes de données (Composant, Fil, Projet)
│   ├── project_service.py  # Sauvegarde/Chargement des projets
│   └── electrical_net_resolver.py
├── simulator/              # Moteur de simulation backend
│   ├── engine.py           # Orchestrateur central
│   ├── runtime.py          # Sandbox d'exécution du script utilisateur
│   ├── gpio.py, i2c.py...  # Gestionnaires de bus
│   ├── devices/            # Logique bas niveau des composants (ex: ssd1306.py)
│   └── modules/            # Bibliothèques MicroPython falsifiées (machine.py, time.py)
├── ui/                     # Interface graphique (PySide6)
│   ├── main_window.py      # Fenêtre principale, Menus, Docks
│   ├── canvas/             # Rendu graphique 2D (QGraphicsScene)
│   │   ├── circuit_scene.py
│   │   └── items/          # Dessin des composants (led_item.py, oled_item.py)
│   └── editor/             # Éditeur de code source colorisé
└── application/
    └── education/          # Moteur de TP, analyse AST, Feedbacks pédagogiques
```

---

## 8. Robustesse et Assurance Qualité (QA)
L'application v1.0 est couverte par une suite de **360+ tests automatisés (`pytest`)**.
Le moteur est immunisé contre :
1. **Les courts-circuits** matériels (isolés par l'ERC de la topologie).
2. **Les boucles infinies** logicielles (gérées par le thread de la Sandbox).
3. **Les appels API invalides** (ex: bus I2C inexistant, adressage mémoire hors-limites).
4. **Les fuites mémoire (Memory Leaks)** lors des redémarrages successifs du moteur.
