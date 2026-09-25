import pytest
from esp32_lab.application.education.exercises.catalog import ExerciseCatalog
from esp32_lab.application.education.exercises.repository import ExerciseRepository

def test_migrated_exercises_load():
    repo = ExerciseRepository()
    catalog = ExerciseCatalog(repo)
    catalog.load_defaults()
    
    exercises = catalog.get_available_exercises()
    
    # Check that we loaded the default 01_led_gpio + the 5 migrated ones
    assert len(exercises) >= 6
    
    # Check that they all have missions and titles
    for ex in exercises:
        assert ex.title
        assert ex.mission.objective
        assert ex.difficulty in ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
        
        # Verify JSON serialization works (Round-Trip tested generally, but just double check string generation)
        json_str = ex.to_json()
        assert "id" in json_str
        assert "mission" in json_str

def test_prerequisites_and_skills():
    repo = ExerciseRepository()
    catalog = ExerciseCatalog(repo)
    catalog.load_defaults()
    
    ex_1 = repo.get("ex_1_gpio_led")
    if ex_1:
        assert "GPIO" in ex_1.skills
        
    ex_3 = repo.get("ex_3_pot_adc")
    if ex_3:
        assert "ADC" in ex_3.skills
