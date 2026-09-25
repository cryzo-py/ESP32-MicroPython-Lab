# PHASE 6.0-F UI AUDIT

## 1. Existant (`esp32_lab/ui/main_window.py`)
- L'interface utilise actuellement un `QVBoxLayout` global avec un `QStackedWidget` pour basculer entre une vue de bienvenue (`WelcomeView`) et une vue laboratoire (`WorkspaceView`).
- La `WorkspaceView` est construite autour d'un `QSplitter` horizontal divisant l'écran en deux grandes zones :
  - **Gauche :** Éditeur de code (QTabWidget) en haut, et Outils de debug (Console, REPL, Propriétés) via un `QSplitter` vertical en bas.
  - **Droite :** Vue du circuit (`CircuitView`) avec une barre d'outils (Zoom, Composants, Grille).
- L'intégration de la gestion d'exécution se fait via les boutons *Run*, *Stop*, *Reset* dans la barre d'actions sous l'éditeur de code.
- Aucun panneau pédagogique n'existe actuellement.

## 2. À Réutiliser
- **`CircuitView` / `CircuitScene`** : Ne sera pas modifié. Gère le drag & drop et l'affichage.
- **`CodeEditor`** : Intégration de l'éditeur Monaco/QScintilla, restera l'outil de code.
- **Boutons d'exécution** : (▶ Simuler, ■ Arrêter). Ils piloteront toujours le `SimulationEngine`.
- **Mécanique de projet (`ProjectModel`)** : Le Starter Project d'un exercice écrasera proprement l'état actuel de la vue.

## 3. À Créer (Panneaux Pédagogiques)
1. **`ExerciseBrowser`** : Un panneau de gauche permettant de naviguer dans le `ExerciseCatalog`. Gère le verrouillage via la progression.
2. **`MissionPanel` & `ObjectivesPanel`** : À intégrer soit dans une barre latérale droite, soit dans un onglet dédié au-dessus du code, affichant les données du `Exercise` courant.
3. **`FeedbackPanel` / `HintPanel`** : Une vue surgissante ou superposée lorsqu'un "Submit" (✓ Vérifier) est cliqué.
4. **`ProgressionPanel`** : Un onglet ou panneau montrant l'état des compétences.

## 4. Architecture d'Intégration UI Cible
Pour ne pas saturer l'espace de l'étudiant, l'architecture suivante sera privilégiée :
- **Left Panel (Nouveau QSplitter 1)** : `ExerciseBrowser` (Liste des TPs). Ce panneau peut être réduit/replié.
- **Center Panel (Existant)** : `CodeEditor` + `CircuitView` (L'espace de travail reste central).
- **Right Panel (Nouveau QSplitter 2)** : `MissionPanel` (Objectifs) + Bouton d'évaluation **✓ Vérifier (Submit)**. Si l'exercice est validé, les `FeedbackPanel` s'affichent ici.

## 5. À Supprimer / Remplacer
- La logique en dur de chargement des anciens exemples via `create_blink_example()`. L'UI doit désormais charger des fichiers JSON via `ExerciseEngine.load_exercise()`.
- Le couplage direct entre le bouton de lancement et un composant précis ; tout passera par l'orchestrateur (ExerciseEngine).
