from typing import Dict, Any
from .models import Exercise, ExerciseMission, LearningObjective, Prerequisite
from .validator import ExerciseValidator

class ExerciseLoader:
    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> Exercise:
        is_valid, errors = ExerciseValidator.validate(data)
        if not is_valid:
            raise ValueError(f"Exercice invalide : {errors}")
            
        m_data = data["mission"]
        mission = ExerciseMission(
            context=m_data["context"],
            mission=m_data["mission"],
            constraints=m_data.get("constraints", []),
            objective=m_data["objective"]
        )
        
        ex = Exercise(
            id=data["id"],
            title=data["title"],
            summary=data.get("summary", ""),
            mission=mission,
            difficulty=data.get("difficulty", "BEGINNER")
        )
        ex.evaluation_rules = data.get("evaluation_rules", [])
        ex.skills = data.get("skills", [])
        return ex
