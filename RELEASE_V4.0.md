# 🚀 ESP32 & Arduino Lab — Version 4.0.0 (Mise à jour Majeure Multi-Cartes & Multi-Langages)

Nous sommes fiers d'annoncer la sortie officielle de la **Version 4.0.0** d'**ESP32 & Arduino Lab**. Cette mise à jour majeure transforme la plateforme en un environnement universel d'apprentissage de l'électronique et de la programmation embarquée, alliant la puissance de l'**ESP32** et la simplicité pédagogique de l'**Arduino Uno R3**, avec prise en charge conjointe de **MicroPython** et du **C++ Arduino**.

---

## ✨ 1. Support Multi-Cartes Natif (ESP32 DevKit & Arduino Uno R3)
- **Arduino Uno R3 (ATmega328P)** : Modélisation graphique et électrique complète (tension logique 5V, ADC 10 bits 0–1023, PWM 8 bits 0–255, broches D0 à D13, A0 à A5, LED intégrée sur D13).
- **ESP32 DevKit v1** : Modélisation complète 30/38 broches (tension logique 3.3V, ADC 12 bits 0–4095, PWM 10 bits 0–1023, LED intégrée sur GPIO2, WiFi, Bluetooth, capteurs tactiles).
- **Sélecteur de carte dynamique** : Bascule instantanée entre ESP32 et Arduino Uno avec adaptation automatique des broches, des tensions de référence et des bibliothèques d'exemples.

---

## 💻 2. Double Environnement de Programmation & Simulation Hybride
- **Onglets de code synchronisés** : L'interface intègre désormais deux éditeurs dédiés :
  - `🐍 main.py` pour le code **MicroPython**.
  - `⚡ sketch.ino` pour le code **Arduino C++** natif (`setup()`, `loop()`, `pinMode()`, `digitalWrite()`, `analogRead()`, `analogWrite()`, `delay()`, etc.).
- **Grisement intelligent** : En mode Arduino Uno, l'onglet MicroPython est automatiquement grisé avec une info-bulle explicative, guidant immédiatement l'élève vers le code C++.
- **Moteur C++ sandboxé et sécurisé** : L'interpréteur C++ intégré analyse l'AST et exécute le sketch en sandbox étanche, sans risque d'accès aux objets Python internes de l'application hôte.
- **Téléversement physique universel** :
  - Téléversement direct MicroPython vers cartes ESP32 physiques.
  - Téléversement direct C++ via `arduino-cli` avec routage automatique du FQBN selon la cible sélectionnée (`arduino:avr:uno` ou `esp32:esp32:esp32`).

---

## 🎓 3. Deux Éditions Distinctes de Déploiement
Pour répondre parfaitement aux besoins en milieu scolaire :
- **🎓 Édition Élève (`ESP32_Lab_Student`)** :
  - Identification obligatoire en début d'épreuve (Nom, Prénom, Classe).
  - Gestion du temps avec chronomètre d'examen et verrouillage automatique à échéance.
  - Verrouillage inviolable des composants et câbles imposés par le sujet.
- **👨‍🏫 Édition Enseignant Studio (`ESP32_Lab_Teacher`)** :
  - Studio complet de conception de travaux pratiques et de sujets de devoir.
  - Définition de barèmes, critères de validation automatique et injection de pannes.
  - Correction, notation assistée et génération de comptes-rendus PDF/DOCX.

---

## ⚡ 4. Moteur Électrique & Topologique Renforcé
- **Détection stricte de circuit fermé** : Une LED ou un actionneur ne peut s'activer que si la maille électrique est complète (chemin fermé VCC -> Anode -> Cathode -> Résistance -> GND). La déconnexion en temps réel du fil de masse (GND) éteint instantanément le composant.
- **Calculs physiques réalistes** : Prise en charge des ponts diviseurs de tension pour potentiomètres et photorésistances (LDR), asservissement angulaire des servomoteurs par signaux PWM, et calcul de résistance équivalente.
- **Précision de sélection & ergonomie** :
  - Distance euclidienne pour la sélection fine des câbles Dupont.
  - Le clic ou la manipulation sur le corps d'un composant inséré sur la breadboard (molette de potentiomètre, poussoir, LED) n'est plus intercepté par les trous sous-jacents de la platine.

---

## 🛡️ 5. Fiabilité, Stabilité & Sécurité Certifiées
- **Arrêt coopératif sans `terminate()`** : Élimination intégrale des appels `QThread.terminate()` dans les moteurs MicroPython et Arduino au profit de signaux d'annulation coopératifs et d'un transformateur AST de boucle. Zéro crash de mémoire ou blocage de thread Qt.
- **Couverture de tests exhaustive** : **520 tests automatisés validés à 100%** sur l'ensemble des modules (topologie, physique, ERC, sandbox, interface graphique et évaluation).

---

## 📦 6. Installation & Téléchargements
Les fichiers exécutables pré-compilés et installeurs tout-en-un sont disponibles dans la section **Releases** de ce dépôt :
- `ESP32_Arduino_Lab_Student_v4.0.exe` (Installeur Windows Élève)
- `ESP32_Arduino_Lab_Teacher_Studio_v4.0.exe` (Installeur Windows Enseignant Studio)
- Versions portables autonomes prêtes pour clés USB dans les archives `.zip`.
