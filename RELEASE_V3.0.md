# 🚀 ESP32 MicroPython Lab - Version 3.0 (Mise à jour Pédagogique Majeure)

Nous sommes ravis d'annoncer la sortie de la **Version 3.0** d'ESP32 MicroPython Lab. Cette mise à jour transforme complètement le simulateur en une véritable **plateforme éducative** conçue pour les enseignants, les écoles et l'auto-apprentissage, tout en renforçant la stabilité et le réalisme physique du laboratoire.

## 🎓 Nouvel Espace Enseignant & Mode Élève
L'application intègre désormais une séparation claire des rôles pour sécuriser les évaluations et les examens.
- **Tableau de Bord Enseignant** : Une interface dédiée, accessible via un code PIN (Menu > Outils > Espace Enseignant), pour centraliser la création et la gestion des travaux pratiques.
- **Assistant de Création (Wizard)** : Un outil étape-par-étape pour créer rapidement des TP, des Exercices ou des Examens avec un titre, une durée (minuteur), et un énoncé détaillé.
- **Environnement Sécurisé** : En mode Élève, l'interface est épurée pour se concentrer sur l'essentiel. Les options de triche ou de modification du cahier des charges sont inaccessibles.

## 🔒 Système de Verrouillage Matériel Avancé
Les professeurs peuvent désormais concevoir des platines de test inviolables pour évaluer la capacité des élèves à programmer un circuit figé :
- **Verrouillage des Composants** : Empêchez le déplacement ou la suppression de la LED, de la résistance ou des capteurs.
- **Soudure Virtuelle (Câbles)** : Verrouillez individuellement les câbles Dupont. L'outil Cadenas ajoute un marqueur (🔒) sur les câbles. En mode Élève, ces câbles ne peuvent plus être débranchés ni supprimés avec la touche Suppr.

## 🎨 Refonte de l'Interface & Accessibilité
- **Nouveau Menu Outils** : Un menu "Outils" dédié remplace les anciennes options dispersées, permettant un accès rapide aux Paramètres et au mode Auteur.
- **Paramètres Centralisés** : Nouvelle fenêtre ergonomique pour basculer facilement entre le Thème Clair et Sombre, changer la langue, et définir le répertoire de sauvegarde par défaut.
- **Contraste & Mode Sombre** : Correction complète des problèmes de contraste ("noir sur bleu") et du texte "blanc sur blanc" sur l'ensemble de l'interface et du panneau d'activité.
- **Support Universel des Caractères (UTF-8)** : Résolution définitive des problèmes d'encodage sous Windows, assurant un rendu parfait des emojis de l'interface (📁, ✏️, 🔒) sur tous les systèmes d'exploitation.

## 🛠️ Améliorations de Stabilité & Corrections de Bugs
- **Logique de Câblage** : Correction d'un bug où la manipulation rapide d'un embout de fil provoquait un comportement inattendu lors du glisser-déposer.
- **Gestion des Sessions** : L'enregistrement d'un TP génère désormais un identifiant unique (UUID). Cela garantit qu'un élève puisse enchaîner plusieurs examens consécutifs sans que le système n'écrase son avancement.
- **Chargement de Projets** : L'ouverture d'un fichier met désormais correctement à jour les permissions physiques du circuit pour refléter immédiatement le statut de verrouillage.

## 📦 Notes pour l'Installation
Un installateur repensé (Inno Setup) est disponible. Pour la mise à jour depuis la V2.0, l'installateur s'occupera d'écraser proprement les anciens fichiers tout en préservant vos projets locaux (.lab32).
