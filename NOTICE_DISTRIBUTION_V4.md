# 📦 Notice de Distribution & Guide de Déploiement — V4.0.0
## ESP32 & Arduino Lab (Éditions Élève & Teacher Studio)

---

### 1. Présentation de la Version 4.0.0

**ESP32 & Arduino Lab v4.0.0** est un environnement d'apprentissage et de simulation électronique complet, autonome et hautement sécurisé, conçu pour les collèges, lycées professionnels, classes préparatoires, IUT et universités.

Cette version 4.0.0 marque une évolution majeure :
- **Prise en charge multi-cartes native** : ESP32 DevKit v1 (3.3V, ADC 12 bits 0–4095, PWM 10 bits 0–1023) et Arduino Uno R3 (5V, ADC 10 bits 0–1023, PWM 8 bits 0–255).
- **Double moteur de simulation logicielle** :
  - **MicroPython** : exécution sandboxée avec transformateur d'interruption AST sans blocage de boucle.
  - **Arduino C++** : interpréteur C++ sandboxé natif avec support complet de `setup()`, `loop()`, `pinMode()`, `digitalWrite()`, `analogRead()`, `analogWrite()`, etc.
- **Téléversement physique matériel** :
  - MicroPython sur ESP32 via le protocole série intégré.
  - Arduino C++ vers matériel réel via `arduino-cli` avec routage automatique du FQBN selon la carte sélectionnée (`esp32:esp32:esp32` ou `arduino:avr:uno`).
- **Fiabilité & Sécurité certifiées** :
  - Suppression intégrale des appels `QThread.terminate()` : arrêts de simulation 100% coopératifs, prévenant toute corruption de mémoire ou crash Qt.
  - Isolation sandboxée interdisant l'accès aux attributs internes Python depuis les sketchs C++.
  - 520 tests automatisés validés à 100% sur 9 suites de tests.

---

### 2. Les Deux Éditions de Distribution

Le projet est distribué sous la forme de deux exécutables distincts pour répondre aux besoins pédagogiques :

| Caractéristique | 🎓 Édition Élève (`Student`) | 👨‍🏫 Édition Enseignant (`Teacher Studio`) |
| :--- | :---: | :---: |
| **Binaire autonome** | `dist/ESP32_Arduino_Lab_Student/ESP32_Arduino_Lab_Student.exe` | `dist/ESP32_Arduino_Lab_Teacher_Studio/ESP32_Arduino_Lab_Teacher_Studio.exe` |
| **Installeur Inno Setup** | `ESP32_Arduino_Lab_Student_v4.0.exe` | `ESP32_Arduino_Lab_Teacher_Studio_v4.0.exe` |
| **Identification de session** | Oui (Nom, Prénom, Classe obligatoires) | Non (Accès direct auteur) |
| **Chronomètre & Verrouillage examen** | Actif (verrouille le montage à expiration) | Contrôle auteur & Réinitialisation |
| **Conception de TP / Missions** | Masquée | Complète (Création, barèmes, critères ERC) |
| **Évaluation & Notation** | Masquée | Complète (Sauvegarde notes & annotations) |
| **Accès au matériel physique** | Lecture & Téléversement direct | Configuration, détection & téléversement |

---

### 3. Prérequis Système & Dépendances

#### A. Matériel et Système d'Exploitation
- **Système d'exploitation** : Windows 10 (64 bits) ou Windows 11 (64 bits).
- **Processeur** : Intel Core i3 / AMD Ryzen 3 ou supérieur recommandé.
- **Mémoire RAM** : 4 Go minimum (8 Go recommandés pour des montages denses).
- **Espace disque libre** :
  - Version portable : environ 250 Mo par édition.
  - Version installée avec Arduino CLI et cœurs de cartes : ~1,5 Go.

#### B. Pilotes USB Série (pour téléversement sur carte réelle)
Pour piloter des cartes physiques connectées en USB :
- **Puce CP2102 / CP2104** (ESP32 DevKit standard) : [Pilote Silicon Labs CP210x](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
- **Puce CH340G / CH341** (clones Arduino Uno et certains ESP32) : [Pilote WCH CH341SER](http://www.wch-ic.com/downloads/CH341SER_EXE.html)
- **Arduino Uno officiel (ATmega16U2)** : les pilotes sont fournis automatiquement par Windows Update ou l'IDE Arduino.

#### C. Compilation Arduino Physique (Optionnelle)
La simulation fonctionne **100% hors ligne sans aucun outil tiers**.
Pour téléverser du code C++ sur une vraie carte Uno ou ESP32 :
1. Installer [Arduino CLI](https://arduino.github.io/arduino-cli/latest/installation/).
2. Vérifier que `arduino-cli` est présent dans le `PATH` de Windows.
3. Installer les cœurs correspondants :
   ```powershell
   arduino-cli core install arduino:avr
   arduino-cli core install esp32:esp32
   ```

---

### 4. Procédure de Compilation & Génération des Releases

Un script automatisé PowerShell est fourni à la racine du projet : `scripts/build_release_v4.ps1`.

#### Étape 1 — Lancer la compilation complète
Ouvrez un terminal PowerShell en mode Administrateur ou standard et exécutez :

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_release_v4.ps1
```

#### Étape 2 — Ce que fait le script :
1. **Nettoyage automatique** des dossiers résiduels `build/` et `dist/`.
2. **Exécution de PyInstaller** avec le fichier de configuration certifié `esp32_lab.spec` :
   - Inclut l'ensemble des modules Python, des profils de cartes JSON (`esp32_devkit.json`, `arduino_uno.json`), des icônes et styles.
   - Génère les deux distributions autonomes :
     - `dist/ESP32_Arduino_Lab_Student/`
     - `dist/ESP32_Arduino_Lab_Teacher_Studio/`
3. **Vérification d'intégrité** : vérifie la présence et la taille des fichiers exécutables générés.
4. **Compilation des installeurs Inno Setup** (si `iscc.exe` est installé sur la machine) :
   - Génère `dist_installer/ESP32_Arduino_Lab_Student_v4.0.exe`
   - Génère `dist_installer/ESP32_Arduino_Lab_Teacher_Studio_v4.0.exe`

---

### 5. Déploiement en Salle de Classe / Établissement

Deux modes de déploiement sont envisageables selon l'infrastructure de l'établissement :

#### Mode A : Déploiement Réseau ou Clé USB (Mode Portable - Recommandé)
Les dossiers générés dans `dist/` sont **totalement portables et sans dépendances** :
1. Copier le dossier `dist/ESP32_Arduino_Lab_Student/` sur le lecteur réseau partagé des élèves (en lecture seule) ou sur les clés USB de TP.
2. Créer un raccourci vers `ESP32_Arduino_Lab_Student.exe` sur le bureau de chaque poste élève.
3. Conserver le dossier `dist/ESP32_Arduino_Lab_Teacher_Studio/` exclusivement sur le poste enseignant ou sur la clé USB du professeur.

#### Mode B : Déploiement par Installeur MSI / EXE (Gestion de parc)
Si vous utilisez un outil de déploiement de logiciels (WAPT, Microsoft Intune, Active Directory GPO) :
1. Déployez `ESP32_Arduino_Lab_Student_v4.0.exe` avec le commutateur silencieux :
   ```cmd
   ESP32_Arduino_Lab_Student_v4.0.exe /VERYSILENT /NORESTART /ALLUSERS
   ```
2. L'installeur associe automatiquement l'extension de fichier `.lab32` et place les raccourcis appropriés sur le bureau.

---

### 6. Format des Fichiers de Projet (`.lab32`)

Le format `.lab32` est un conteneur JSON standardisé qui garantit l'interopérabilité entre les versions :
- **Topologie électrique** : position des cartes, composants (LED, résistances, potentiomètres, servomoteurs, capteurs), fils de câblage et nœuds électriques.
- **Code source** : scripts MicroPython (`main.py`) et sketchs Arduino C++ (`sketch.ino`).
- **Profil de carte actif** : identifiant de la carte (`esp32_devkit` ou `arduino_uno`).
- **Métadonnées pédagogiques** : énoncé de la mission, barème, temps imparti, état de complétion et signature d'intégrité de la copie élève.

---

### 7. Résolution des Problèmes Fréquents (FAQ)

#### Q1 : Windows Defender SmartScreen affiche un avertissement au premier lancement.
- **Cause** : L'exécutable nouvellement compilé n'est pas signé avec un certificat numérique payant EV.
- **Solution** : Cliquer sur **"Informations complémentaires"**, puis sur **"Exécuter quand même"**. Pour un déploiement de masse, ajoutez le dossier de l'application aux exclusions de l'antivirus.

#### Q2 : La carte physique n'apparaît pas dans la liste des ports COM.
- **Solution** : 
  1. Débrancher et rebrancher le câble USB.
  2. Vérifier dans le Gestionnaire de périphériques Windows si un point d'exclamation jaune apparaît sur le port série USB.
  3. Installer le pilote approprié (CP210x ou CH340).
  4. Cliquer sur le bouton **"Rafraîchir les ports"** dans l'application.

#### Q3 : Le bouton "Téléverser Arduino" affiche une erreur "arduino-cli introuvable".
- **Solution** : Téléchargez l'exécutable `arduino-cli.exe` et placez-le dans le dossier de l'application ou ajoutez-le au `PATH` de Windows.

---

### 8. Contacts & Support

- **Développement & Ingénierie** : Équipe ESP32 & Arduino Lab
- **Documentation technique interne** : Consultez `DOCUMENTATION_COMPLETE.md` et `ROADMAP_V4.md`.
- **Rapports d'audit de sécurité** : Consultez l'artéfact `audit_complet_v4_feu_vert.md`.
