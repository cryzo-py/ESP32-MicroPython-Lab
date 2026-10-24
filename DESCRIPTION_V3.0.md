# 🌟 ESP32 MicroPython Lab - Description Détaillée (Version 3.0)

**ESP32 MicroPython Lab** est un logiciel de simulation interactif, hors-ligne et Open-Source, spécialement conçu pour l'apprentissage et l'évaluation de la programmation sur microcontrôleur (ESP32) avec le langage **MicroPython**.

Contrairement aux simulateurs génériques, la **Version 3.0** a été repensée comme une véritable **plateforme technopédagogique**. Elle offre un environnement sécurisé pour faire passer des examens, corriger des copies et gérer des classes, sans nécessiter la moindre connexion Internet ni l'achat de matériel physique.

---

## 🏗️ L'Architecture "Dual-Version"

La grande force de la version 3.0 est sa séparation en deux logiciels distincts, adaptés au rôle de l'utilisateur :

### 1. Teacher Studio (Édition Enseignant)
C'est le *Centre de Contrôle*. Il permet au professeur de concevoir des séquences d'apprentissage de A à Z.
* **Mode Auteur :** Un assistant (Wizard) permet de paramétrer le sujet (Titre, Consignes, Type : TP ou Examen).
* **Contrôle du Temps :** Possibilité d'imposer une limite de temps stricte (Chronomètre).
* **Verrous Pédagogiques :** Le professeur peut pré-câbler des composants sur la platine (ex: un capteur I2C) et les *verrouiller*. L'élève ne pourra ni les déplacer, ni les supprimer.
* **Mode Évaluation :** Une fois le fichier de l'élève récupéré, l'enseignant dispose d'un onglet secret pour lire le code, tester le câblage, attribuer une note (sur un barème défini) et rédiger un commentaire.
* **Gestion des Identifiants (Anti-collision) :** La duplication d'un sujet (Enregistrer sous) génère un nouvel UUID d'activité en arrière-plan, garantissant que les sessions des élèves ne se mélangent jamais dans la base de données.

### 2. Student Edition (Édition Élève)
C'est l'*Espace d'Examen*. L'interface est épurée de toute distraction et l'environnement est sécurisé.
* **Identification Forcée :** Au lancement d'un TP, un écran modal oblige l'étudiant à saisir son *Nom, Prénom et Classe*.
* **Sauvegarde Intelligente :** L'étudiant n'a plus à choisir le nom de son fichier. Au moment du rendu, le logiciel force une nomenclature standardisée (ex: `TP_LED_Dupont_Jean_4S2.lab32`), évitant ainsi les "copies perdues".
* **Sécurité Anti-Triche :** Si un chronomètre est défini, l'élève ne possède pas de bouton "Recommencer".

---

## 🛡️ Le Moteur Anti-Triche (Strict Mode)

Le logiciel embarque un système de persistance locale via une base de données **SQLite (`sessions.db`)**. Ce système garantit l'intégrité d'un examen :
1. **Persistance du Chronomètre :** Si un élève ferme brutalement l'application (Alt+F4) pour tenter de remettre le chronomètre à zéro, la base de données se souvient de son état. À la réouverture, le temps reprend exactement où il s'était arrêté.
2. **Congélation (Freeze) :** Une fois le temps écoulé (ou si l'élève clique sur "Valider mon travail"), l'application passe en état `FROZEN`.
   * *Conséquence 1 :* L'éditeur de code MicroPython bascule en lecture seule.
   * *Conséquence 2 :* La platine de montage est bloquée (impossible d'ajouter, déplacer ou supprimer un composant/câble).

---

## 🔌 Le Moteur de Simulation (Core Engine)

Au cœur de l'application se trouve un simulateur extrêmement fidèle à la réalité matérielle :

* **Moteur MicroPython Sandboxé :** Le code Python écrit par l'élève est exécuté dans un interpréteur virtuel sécurisé. Il intercepte les appels matériels (`machine.Pin`, `machine.PWM`, `machine.Timer`, `machine.ADC`, `machine.I2C`) sans faire planter le logiciel principal.
* **Résolution Topologique (Electrical Nets) :** Le logiciel calcule en temps réel quels composants sont reliés entre eux via la platine d'essai (Breadboard) et les câbles. Si une LED est reliée au GPIO 2 via une résistance, le moteur le détecte physiquement !
* **Composants Dynamiques :** Gestion de composants variés : LEDs classiques, LEDs RGB, Boutons, Potentiomètres (ADC), Servomoteurs (PWM), Écrans OLED (I2C), Capteurs BME280 (I2C/SPI), etc.
* **Interruptions (IRQs) :** Prise en charge des interruptions matérielles (`IRQ_RISING`, `IRQ_FALLING`) pour simuler parfaitement les rebonds et les déclencheurs de boutons.

---

## 🖥️ L'Interface Utilisateur (UI)

Basée sur **PySide6 (Qt)**, l'interface est moderne, fluide et divisée en zones logiques :

1. **Panneau Pédagogique (Gauche) :** Affiche les consignes, l'identité de l'élève, l'état d'avancement et l'énorme chronomètre.
2. **Zone de Câblage (Milieu) :** Un canevas 2D interactif (Drag & Drop) comprenant une platine d'essai photoréaliste. Les points d'ancrage (Snapping) facilitent le placement des fils.
3. **Éditeur de Code (Droite) :** Un éditeur de texte enrichi avec coloration syntaxique complète pour Python, numérotation des lignes et console de sortie intégrée pour voir les `print()` et les erreurs (`Traceback`).
4. **Outils d'Analyse :** (Optionnels) Un oscilloscope virtuel et un vérificateur de règles électriques (ERC) pour aider au débogage.

---

## 🛠️ Stack Technique & Déploiement

* **Langage & Framework :** Python 3.11, PySide6 (Interface Graphique).
* **Base de données :** SQLite (pour la persistance des sessions et des profils).
* **Format de fichier :** `.lab32` (Archive JSON structurée contenant le profil pédagogique, le code source, et les coordonnées spatiales de la topologie du circuit).
* **Distribution :** Compilé avec **PyInstaller** et empaqueté avec **Inno Setup** pour fournir des exécutables d'installation (`.exe`) totalement autonomes pour Windows. Aucune installation de Python n'est requise sur les machines du lycée.

## 🏁 Conclusion

**ESP32 MicroPython Lab v3.0** n'est pas seulement un simulateur d'électronique. C'est le **compagnon pédagogique ultime** pour les professeurs de technologie, NSI, SNT ou Sciences de l'Ingénieur. Il résout les problèmes logistiques (manque de matériel, composants grillés), de gestion informatique (noms de fichiers exotiques) et d'évaluation (triche, notation laborieuse), tout en offrant aux élèves une expérience de code immersive et réaliste.
