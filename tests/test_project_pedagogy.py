import json
import pytest
from esp32_lab.core.models.project import ProjectModel

def test_project_model_backward_compatibility():
    # Ancien format JSON sans pedagogy_profile
    old_data = {
        "version": 1,
        "id": "1234",
        "name": "Ancien Projet",
        "board_id": "esp32_wroom_32"
    }
    
    project = ProjectModel.from_dict(old_data)
    assert project.name == "Ancien Projet"
    assert project.pedagogy_profile is None
    
    # Serialisation d'un ancien projet (ne doit pas inclure pedagogy_profile)
    new_data = project.to_dict()
    assert "pedagogy_profile" not in new_data

def test_project_model_with_pedagogy():
    profile = {
        "schema_version": "1.0",
        "mission": {"title": "TP 1"}
    }
    
    project = ProjectModel(name="Nouveau TP", pedagogy_profile=profile)
    data = project.to_dict()
    
    assert "pedagogy_profile" in data
    assert data["pedagogy_profile"]["mission"]["title"] == "TP 1"
    
    # Deserialisation
    loaded_project = ProjectModel.from_dict(data)
    assert loaded_project.pedagogy_profile is not None
    assert loaded_project.pedagogy_profile["schema_version"] == "1.0"
