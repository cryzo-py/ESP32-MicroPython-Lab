from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class LearningObjective:
    id: str
    title: str
    description: str
    skill: str
    level: str # BEGINNER, INTERMEDIATE, ADVANCED

@dataclass
class Prerequisite:
    skill: str
    minimum_level: str # PRACTICING, MASTERED

@dataclass
class ExerciseMission:
    context: str
    mission: str
    constraints: List[str]
    objective: str

@dataclass
class Exercise:
    id: str
    title: str
    summary: str
    mission: ExerciseMission
    difficulty: str
    schema_version: str = "1.0"
    lesson_id: Optional[str] = None
    estimated_duration: int = 15
    learning_objectives: List[LearningObjective] = field(default_factory=list)
    prerequisites: List[Prerequisite] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    starter_project: Optional[Dict[str, Any]] = None  # Or project ID
    evaluation_rules: List[Dict[str, Any]] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    allow_solution: bool = False
    solution_code: Optional[str] = None
    solution_description: Optional[str] = None
    
    def to_json(self) -> str:
        # Simplistic serializer for testing
        return json.dumps({
            "id": self.id,
            "title": self.title,
            "schema_version": self.schema_version,
            "mission": {
                "context": self.mission.context,
                "mission": self.mission.mission,
                "constraints": self.mission.constraints,
                "objective": self.mission.objective
            },
            "difficulty": self.difficulty
        })

@dataclass
class LearningPath:
    id: str
    title: str
    exercises: List[str] = field(default_factory=list)
    
    def next_exercise(self, current_id: str) -> Optional[str]:
        if current_id in self.exercises:
            idx = self.exercises.index(current_id)
            if idx + 1 < len(self.exercises):
                return self.exercises[idx + 1]
        return None
        
    def previous_exercise(self, current_id: str) -> Optional[str]:
        if current_id in self.exercises:
            idx = self.exercises.index(current_id)
            if idx - 1 >= 0:
                return self.exercises[idx - 1]
        return None
        
    def completion_percentage(self, completed_exercises: List[str]) -> float:
        if not self.exercises:
            return 0.0
        completed = set(self.exercises).intersection(completed_exercises)
        return (len(completed) / len(self.exercises)) * 100.0
        
    def is_available(self, exercise_id: str, completed_exercises: List[str]) -> bool:
        # Simplistic: Available if it's the first or the previous one is completed
        if exercise_id not in self.exercises:
            return False
        idx = self.exercises.index(exercise_id)
        if idx == 0:
            return True
        return self.exercises[idx - 1] in completed_exercises
    
class ExerciseState:
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    MASTERED = "MASTERED"
