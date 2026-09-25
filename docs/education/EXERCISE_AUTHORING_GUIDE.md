# Guide de Création d'Exercices (Authoring Guide)

Ce guide s'adresse aux enseignants souhaitant créer de nouveaux exercices pour l'**ESP32 MicroPython Lab**.

## 1. Principes
Le système d'évaluation est **Data-Driven**. L'enseignant n'a plus besoin d'écrire du code Python complexe pour évaluer le travail d'un étudiant. Tout est défini dans un fichier JSON situé dans `esp32_lab/application/education/exercises/data/`.

## 2. Structure
Un exercice comprend :
- Une **Mission** : L'énoncé affiché à l'étudiant.
- Un **Starter Project** (optionnel) : Un état initial du montage (composants, fils, code de base).
- Des **Règles d'évaluation** : Les critères de réussite (Topologie physique, AST de code, Composants).
- Des **Indices (Hints)** : Une liste d'indices progressifs affichés en cas d'échec.

## 3. Comment Créer un Exercice
1. **Créer le fichier** : Créez un fichier `.json` dans `exercises/data/` (ex: `mon_exercice.json`).
2. **Définir l'ID** : Il doit être unique (ex: `ex_i2c_scanner`).
3. **Configurer la Topologie** : Si vous voulez que l'étudiant câble un composant (ex: un bouton sur le GPIO 4), ajoutez une règle :
   ```json
   {
      "id": "rule_top",
      "type": "topology",
      "gpio": 4,
      "component_type": "button"
   }
   ```
4. **Vérifier** : Relancez l'application. Le catalogue (`ExerciseCatalog`) chargera et validera automatiquement votre JSON. S'il y a une erreur de format, l'exercice sera ignoré (sans crasher l'application) et une erreur sera affichée dans les logs.

## 4. Astuces Pédagogiques
- Ne donnez pas la solution dans le premier Hint.
- Préférez la règle `topology` à la vérification naïve des fils. L'étudiant a le droit d'utiliser 15 jumpers et 3 colonnes de breadboard si le signal électrique arrive bien au composant final !
- L'AST (`code_pin`) permet de lire le code de manière intelligente (les commentaires et espaces sont ignorés).
