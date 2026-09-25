# PHASE 6.0-F UI GUIDE

## 1. Architecture d'Intégration
L'interface pédagogique a été injectée sans altérer l'architecture centrale de la fenêtre PySide6, afin de préserver l'historique et la robustesse de l'espace de travail. 

Le script d'orchestration **`education_orchestrator.py`** est appelé à l'initialisation de `MainWindow`.
Il initialise :
- `ExerciseCatalog`
- `ExerciseEngine`
- `ProgressionEngine`
- `EvaluationEngine`
- `DiagnosisEngine`
- `FeedbackEngine`

## 2. Panels Pédagogiques

### `ExerciseBrowser` (Gauche)
- Injecté dans un `QTabWidget` au-dessus de la bibliothèque de composants.
- Affiche l'arborescence des exercices issus des fichiers JSON.
- Les exercices maîtrisés sont affichés avec un `✓` vert.
- Les exercices verrouillés par prérequis sont affichés avec un cadenas `🔒`.

### `MissionPanel` (Droite)
- Injecté à droite de la `CircuitScene`.
- Affiche le contexte, la consigne (`mission`), les contraintes, et les objectifs (`rules`).
- Les objectifs sont traduits du JSON en instructions lisibles via `_translate_rule()`.
- Contient le bouton **✓ Vérifier l'exercice** qui déclenche l'évaluation `_on_submit()`.

### `FeedbackPanel` (Droite, sous la Mission)
- Caché par défaut. 
- Apparaît suite à un "Submit" pour afficher le résultat :
  - **Échec** : Affiche le premier diagnostic, la cause, l'explication pédagogique, et permet de demander des **Indices (💡)** ou de **Réessayer (↻)**.
  - **Succès** : Affiche un message de félicitations et permet de **Continuer (➔)**.

## 3. Workflow de Soumission
1. **Submit** : Sauvegarde le code depuis le `CodeEditor` dans le `ProjectModel`. 
2. Met à jour l'`ElectricalNetResolver` du `SimulationEngine`.
3. Lance `ExerciseEngine.submit_exercise()`.
4. Émet `exercise_state_changed` qui déclenche l'affichage dans `FeedbackPanel`.

## 4. Nettoyage et Navigation
- Le chargement d'un exercice instancie son projet initial (`starter_project`) via le constructeur dynamique.
- Les anciens composants sont supprimés (grâce au comportement standard de `load_project`).
- La progression (tentatives et réussites) est sauvegardée par `ProgressionEngine` entre les changements d'exercices.
