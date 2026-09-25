# ESP32 MicroPython Lab - Exercise Schema

Ce document décrit le schéma attendu pour un fichier JSON représentant un exercice dans `ExerciseEngine`.

```json
{
  "id": "ex_1_gpio_led",
  "title": "TP 1 : LED Clignotante",
  "summary": "Faire clignoter une LED avec l'ESP32.",
  "difficulty": "BEGINNER",
  "skills": ["GPIO", "TOPOLOGY"],
  "mission": {
    "context": "Context optionnel de l'exercice...",
    "mission": "Consigne principale pour l'étudiant.",
    "objective": "Objectif pédagogique global.",
    "constraints": ["Ne pas utiliser delay"]
  },
  "evaluation_rules": [
    {
      "id": "rule_code_pin",
      "type": "code_pin",
      "gpio": 2,
      "mode": "OUT",
      "weight": 50
    },
    {
      "id": "rule_topology",
      "type": "topology",
      "gpio": 2,
      "component_type": "led",
      "pin_name": "anode",
      "weight": 50
    }
  ],
  "hints": [
    "Avez-vous bien connecté la LED ?",
    "Vérifiez que le code utilise le bon GPIO."
  ],
  "starter_project": {
    "components": [],
    "connections": [],
    "files": {
      "main.py": "print('Code de base')"
    }
  }
}
```

## Types de Règles (Evaluation Rules)
1. `code_pin` : Utilise l'AST pour vérifier la déclaration d'une broche (ex: `Pin(2, Pin.OUT)`).
2. `topology` : Utilise `ElectricalNetResolver` pour vérifier qu'un GPIO est physiquement connecté à un pin spécifique d'un composant donné.
3. `component` : Vérifie la présence d'un composant sur le plan de travail.
