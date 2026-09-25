from typing import List
from .models import Exercise
from .repository import ExerciseRepository
from .loader import ExerciseLoader

class ExerciseCatalog:
    """Manages the built-in pedagogical exercises catalog."""
    
    def __init__(self, repository: ExerciseRepository):
        self.repository = repository
        
    def load_defaults(self):
        # 01 - LED GPIO
        data = {
            "id": "01_led_gpio",
            "title": "LED contrôlée par GPIO2",
            "summary": "Allume une LED sur le port GPIO2.",
            "difficulty": "BEGINNER",
            "skills": ["GPIO", "TOPOLOGY"],
            "mission": {
                "context": "Les GPIO permettent de contrôler des composants.",
                "mission": "Construis un montage allumant une LED.",
                "constraints": ["Utiliser GPIO2", "Utiliser une résistance"],
                "objective": "La LED s'allume avec le code approprié."
            },
            "evaluation_rules": [
                {
                    "id": "rule_code",
                    "type": "code_pin",
                    "gpio": 2,
                    "mode": "OUT",
                    "weight": 50
                },
                {
                    "id": "rule_top",
                    "type": "topology",
                    "gpio": 2,
                    "component_type": "led",
                    "pin_name": "anode",
                    "weight": 50
                }
            ]
        }
        
        ex = ExerciseLoader.load_from_dict(data)
        self.repository.save(ex)
        
        # Load from JSON files
        import os
        import json
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as f:
                        ex_data = json.load(f)
                        try:
                            ex = ExerciseLoader.load_from_dict(ex_data)
                            self.repository.save(ex)
                        except Exception as e:
                            print(f"Failed to load {filename}: {e}")
        
    def get_available_exercises(self) -> List[Exercise]:
        return self.repository.get_all()
