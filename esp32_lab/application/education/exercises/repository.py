from typing import Dict, List, Optional
from .models import Exercise, LearningPath

class ExerciseRepository:
    def __init__(self):
        self._exercises: Dict[str, Exercise] = {}
        
    def save(self, exercise: Exercise):
        self._exercises[exercise.id] = exercise
        
    def get(self, exercise_id: str) -> Optional[Exercise]:
        return self._exercises.get(exercise_id)
        
    def get_all(self) -> List[Exercise]:
        return list(self._exercises.values())

class LearningPathRepository:
    def __init__(self):
        self._paths: Dict[str, LearningPath] = {}
        
    def save(self, path: LearningPath):
        self._paths[path.id] = path
        
    def get(self, path_id: str) -> Optional[LearningPath]:
        return self._paths.get(path_id)
