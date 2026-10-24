# 👨‍🏫 Guide d'Utilisation - Édition Enseignant (Teacher Studio)

Bienvenue dans la version Enseignant de **ESP32 MicroPython Lab**. Cette version vous donne les pleins pouvoirs pour concevoir des TP, imposer des contraintes d'examen, et évaluer vos élèves.

## 1. Créer une nouvelle activité (TP ou Examen)
1. Lancez le logiciel via le raccourci **ESP32 Lab - Teacher Studio**.
2. Sur l'écran d'accueil, cliquez sur **"Nouvelle Activité (Mode Auteur)"**.
3. Remplissez le formulaire de la mission :
   - **Titre & Sujet :** Donnez un nom et décrivez le but du TP (ex: "Faire clignoter la LED rouge").
   - **Type :** Choisissez entre *Exercice Libre*, *Travail Pratique (TP)* ou *Examen*.
   - **Temps alloué :** Indiquez le temps en minutes (mettez `0` pour un temps illimité).
   - **Barème :** Fixez la note maximale (ex: 20).
4. Cliquez sur **Créer**.

## 2. Préparer le matériel pour les élèves
Vous pouvez pré-câbler ou préparer le plan de travail de vos élèves :
1. Allez dans l'onglet **"Montage & Platine"**.
2. Glissez les composants depuis la palette de gauche (ex: un ESP32 et une LED).
3. **Astuce de sécurité (Verrouillage) :** Pour empêcher un élève de supprimer un composant par erreur pendant l'examen, faites un **clic-droit** sur le composant (ex: l'ESP32) et choisissez l'option pour le **Verrouiller**.

## 3. Enregistrer et distribuer le sujet
1. Allez dans le menu **Fichier > Enregistrer sous**.
2. Nommez votre fichier (ex: `Sujet_DS_1.lab32`) et enregistrez-le.
3. Il vous suffit de copier ce fichier sur le réseau du lycée, dans l'ENT ou sur des clés USB pour le distribuer aux élèves.
*Note : Si vous utilisez "Enregistrer sous" pour créer un "Sujet B" à partir d'un "Sujet A", le logiciel génère automatiquement un nouvel identifiant interne sécurisé pour éviter que les copies ne se mélangent.*

## 4. Corriger une copie d'élève
1. Ouvrez le fichier rendu par un élève (ex: `Sujet_DS_1_Dupont_Jean.lab32`).
2. Vous remarquerez que le temps est figé et la copie est en mode "Terminé".
3. *(Optionnel)* Si vous voulez tester le code de l'élève en direct, cliquez sur le bouton rouge **"🔄 Réinitialiser la tentative locale"** dans le panneau gauche.
4. Allez dans le panneau **"Évaluation"** (invisible pour les élèves).
5. Entrez sa note, ajoutez vos appréciations, et cliquez sur **Sauvegarder l'évaluation**. Vous pouvez ensuite lui renvoyer le fichier corrigé !
