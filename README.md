# ⚡ ESP32 MicroPython Lab

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg?style=for-the-badge&logo=python)
![Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-orange.svg?style=for-the-badge&logo=qt)
![License](https://img.shields.io/badge/License-Proprietary%20Non--Commercial-red.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/Tests-186%20passing-brightgreen.svg?style=for-the-badge)

**Environnement Virtuel de Simulation Électronique & de Programmation MicroPython pour ESP32**

*Conçu & Développé par **Fares Bel Haj Ali***

[Fonctionnalités](#-fonctionnalités-clés) •
[Composants](#-bibliothèque-de-composants) •
[Cursus Pédagogique](#-cursus-pédagogique-10-tps) •
[Raccourcis Clavier](#-raccourcis-clavier) •
[Installation](#-installation--démarrage) •
[Licence](#-licence--propriété-intellectuelle)

</div>

---

## 📖 Présentation

**ESP32 MicroPython Lab** est un environnement d'apprentissage interactif complet conçu pour l'enseignement et l'expérimentation de l'électronique embarquée avec le microcontrôleur ESP32 et le langage **MicroPython**.

L'application combine une **platine d'essai MB-102 ultra-réaliste**, un système de câblage Dupont interactif, un interpréteur MicroPython temps réel, une console REPL bidirectionnelle, un oscilloscope simulé, ainsi qu'un **moteur pédagogique d'évaluation automatique** comprenant 10 travaux pratiques (TPs) guidés.

---

## ✨ Fonctionnalités Clés

- 🖥️ **Vue Maquette Réaliste** :
  - Platine d'essai (Breadboard MB-102) standard 830 points avec détection automatique de continuité électrique entre broches et rails d'alimentation (+ / -).
  - Câblage interactif par câbles Dupont mâle-mâle : points de contrôle déplaçables, couleurs configurables, suppression intuitive.
- ⚙️ **Moteur de Simulation MicroPython Temps Réel** :
  - Support des modules officiels : `machine.Pin`, `machine.PWM`, `machine.ADC`, `machine.I2C`, `time.sleep`, `neopixel.NeoPixel`, etc.
  - Exécution en thread isolé avec arrêt immédiat et gestion des boucles infinies.
  - Console REPL interactive connectée à l'interpréteur simulé.
- 🎓 **Cursus Pédagogique Intégré & Auto-Évaluation** :
  - 10 Travaux Pratiques progressifs couvrant les entrées/sorties numériques, analogiques (ADC/PWM), capteurs, affichages et protocoles bus (I2C).
  - Évaluateur d'exercices interactif vérifiant le montage matériel et le code de l'élève.
  - Exportation de comptes-rendus complets au format HTML pour l'enseignant.
- 🎨 **Double Thème Interface Moderne (Dark / Light)** :
  - Mode Sombre haute technologie pour un confort visuel prolongé.
  - Mode Clair haute lisibilité, adapté aux vidéoprojecteurs et à la lumière ambiante.
  - Coloration syntaxique MicroPython personnalisée pour chaque thème.
- 📈 **Outils d'Analyse Intégrés** :
  - Simulateur d'oscilloscope pour visualiser les signaux PWM et temporels.
  - Tableau de bord d'état matériel (Hardware Status) affichant l'état logique de tous les GPIOs.

---

## 🔌 Bibliothèque de Composants

| Composant | Description | Simulation |
| :--- | :--- | :--- |
| **ESP32 WROOM-32** | Carte microcontrôleur 30 broches | GPIOs, ADC, PWM, I2C, SPI |
| **Breadboard MB-102** | Platine d'essai 830 contacts | Lignes A-E, F-J et bus d'alimentation |
| **LED 5mm** | Diode électroluminescente (Rouge, Verte, Bleue, Jaune) | Rendu dynamique de brillance |
| **Résistance** | 220Ω, 330Ω, 1kΩ, 10kΩ, etc. | Bagues de couleur réalistes |
| **Bouton Poussoir** | Tact switch à rappel | Interaction clic / relâchement |
| **Potentiomètre** | Résistance variable analogique | Curseur rotatif avec signal ADC |
| **Servomoteur SG90** | Servomoteur angulaire 0–180° | Pilotage par PWM (50 Hz) |
| **Capteur DHT22** | Capteur de température & humidité | Curseurs de simulation météo |
| **Écran OLED SSD1306** | Afficheur graphique 128x64 pixels | Bus I2C (adresse 0x3C) |
| **Écran LCD 16x2 I2C** | Afficheur alphanumérique HD44780 | Module I2C PCF8574 |
| **Module Relais** | Relais électromécanique 5V | Indicateur LED & commutation |
| **Anneau NeoPixel** | Anneau 8 / 16 / 24 LEDs RGB adressables | Contrôle individuel via module `neopixel` |

---

## 📚 Cursus Pédagogique (10 TPs)

1. **TP 1 : Ma première LED clignotante** — Prise en main des GPIOs en sortie (`machine.Pin.OUT`).
2. **TP 2 : Contrôle interactif par bouton poussoir** — Entrées numériques et résistances de tirage (`PULL_UP`).
3. **TP 3 : Lecture de tension avec le potentiomètre** — Convertisseur Analogique-Numérique (`machine.ADC`).
4. **TP 4 : Pilotage angulaire d'un servomoteur SG90** — Modulation de largeur d'impulsion (`machine.PWM`).
5. **TP 5 : Station Météo avec Capteur DHT22** — Lecture de grandeurs physiques et affichage en temps réel.
6. **TP 6 : Affichage graphique sur écran OLED SSD1306** — Communication bus I2C et tracé de texte/formes.
7. **TP 7 : Mesure de distance par ultrasons (HC-SR04)** — Calcul de temps de vol et conversion métrique.
8. **TP 8 : Afficheur Alphanumérique LCD 16x2 I2C** — Découverte du contrôleur HD44780 et bus série.
9. **TP 9 : Commande de puissance avec module relais** — Isolation galvanique et pilotage de charges externes.
10. **TP 10 : Anneau de LEDs RVB Adressables NeoPixel** — Programmation d'effets lumineux dynamiques (WS2812B).

---

## ⌨️ Raccourcis Clavier

| Raccourci | Action |
| :--- | :--- |
| <kbd>F5</kbd> | **Exécuter le code MicroPython** dans le simulateur |
| <kbd>F6</kbd> | **Arrêter la simulation en cours** |
| <kbd>Ctrl</kbd> + <kbd>N</kbd> | Créer un **Nouveau Projet** |
| <kbd>Ctrl</kbd> + <kbd>O</kbd> | **Ouvrir** un projet existant (`.esp32proj`, `.esp32lab`) |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | **Sauvegarder** le projet actuel |
| <kbd>Ctrl</kbd> + <kbd>B</kbd> | Basculer entre le **Thème Sombre** et le **Thème Clair** |
| <kbd>Suppr</kbd> | Supprimer le fil Dupont ou le composant sélectionné |

---

## 🚀 Installation & Démarrage

### Option 1 : Exécutable Autonome Windows (Recommandé pour les élèves)
Téléchargez l'installeur ou le fichier binaire autonome `ESP32_Lab.exe` depuis la section [Releases]. Aucun prérequis Python n'est nécessaire.

### Option 2 : Exécution depuis les sources Python

#### Prérequis :
- Python 3.10 ou supérieur
- Système d'exploitation : Windows 10/11 (ou Linux/macOS avec support Qt6)

#### 1. Cloner ou télécharger le dépôt :
```bash
git clone https://github.com/cryzo-py/ESP32-MicroPython-Lab.git
cd "esp32-micropython-lab"
```

#### 2. Créer un environnement virtuel (optionnel mais conseillé) :
```bash
python -m venv venv
# Sous Windows :
.\venv\Scripts\activate
```

#### 3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

#### 4. Lancer l'application :
```bash
python run.py
```

#### 5. Lancer la suite de tests automatisés :
```bash
python -m pytest tests/ -q
```

---

## 📦 Compilation de l'Exécutable (`.exe`)

Pour compiler l'application sous Windows en exécutable autonome sans invite de commande :

```bash
python build_exe.py
```
Le binaire final est produit dans le répertoire `dist/ESP32_Lab/ESP32_Lab.exe`.

Pour générer l'installeur d'installation complet Windows :
- Ouvrez `installer.iss` dans **Inno Setup Compiler 6** et cliquez sur **Compile** (ou lancez `iscc installer.iss`).

---

## 👤 Auteur & Contact

**Fares Bel Haj Ali**  
*Ingénieur / Concepteur & Développeur Logiciel*

- 📧 **Email** : [belhadj.fares@gmail.com](mailto:belhadj.fares@gmail.com)
- 📞 **Téléphone** : +216 22 392 646

---

## 📄 Licence & Propriété Intellectuelle

Copyright © 2024–2026 **Fares Bel Haj Ali**. Tous droits réservés.

Ce logiciel est distribué sous **Contrat de Licence Propriétaire d'Utilisation Éducative et Non Commerciale**.  
L'utilisation personnelle et académique (écoles, lycées, universités, fablabs) est **libre et gratuite**.  
Toute utilisation commerciale, revente, monétisation ou distribution modifiée sans autorisation écrite de l'auteur est **strictement interdite**.

Consultez le fichier [LICENSE](LICENSE) pour les conditions juridiques complètes.
