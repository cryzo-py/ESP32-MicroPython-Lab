# -*- coding: utf-8 -*-
import pytest
from esp32_lab.core.models.submission import Submission, SubmissionStatus
from esp32_lab.core.submission_evaluation_service import SubmissionEvaluationService
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.component import ComponentModel

@pytest.fixture
def eval_service():
    return SubmissionEvaluationService()

def test_evaluate_topology_success(eval_service):
    # Success profile: requires a led component
    pedagogy_profile = {
        "criteria": [
            {
                "id": "crit_led",
                "type": "required_component",
                "blocking": True,
                "expected": {"type": "LED"}
            }
        ]
    }
    
    # Project with led
    proj = ProjectModel()
    proj.components.append(ComponentModel(type="LED", id="led_1", x=0, y=0))
    
    sub = Submission(session_id="s1", activity_id="a1", snapshot=proj.to_dict())
    
    res_sub = eval_service.evaluate(sub, pedagogy_profile)
    assert res_sub.status == SubmissionStatus.WAITING_TEACHER
    assert res_sub.evaluation_result["status"] == "SUCCESS"
    assert "crit_led" in res_sub.evaluation_result["criteria"]
    assert res_sub.evaluation_result["criteria"]["crit_led"]["result"] == "PASS"
    assert res_sub.proposed_grade.percentage == 100.0

def test_evaluate_topology_failure(eval_service):
    # Success profile: requires a led component
    pedagogy_profile = {
        "criteria": [
            {
                "id": "crit_led",
                "type": "required_component",
                "blocking": True,
                "expected": {"type": "LED"}
            }
        ]
    }
    
    # Empty project
    proj = ProjectModel()
    
    sub = Submission(session_id="s1", activity_id="a1", snapshot=proj.to_dict())
    
    res_sub = eval_service.evaluate(sub, pedagogy_profile)
    assert res_sub.evaluation_result["status"] == "PARTIAL" # FAIL due to missing LED
    assert res_sub.evaluation_result["criteria"]["crit_led"]["result"] == "FAIL"
    assert res_sub.proposed_grade.percentage == 0.0

def test_evaluate_code_success(eval_service):
    pedagogy_profile = {
        "criteria": [
            {
                "id": "crit_code",
                "type": "code_pin_mode",
                "expected": {"gpio": 18, "mode": "OUT"}
            }
        ]
    }
    
    proj = ProjectModel()
    proj.set_main_code("from machine import Pin\np = Pin(18, Pin.OUT)")
    
    sub = Submission(session_id="s1", activity_id="a1", snapshot=proj.to_dict())
    res_sub = eval_service.evaluate(sub, pedagogy_profile)
    
    assert res_sub.evaluation_result["status"] == "SUCCESS"
    assert res_sub.evaluation_result["criteria"]["crit_code"]["result"] == "PASS"
    assert res_sub.proposed_grade.score == 10
    
def test_evaluate_code_failure(eval_service):
    pedagogy_profile = {
        "criteria": [
            {
                "id": "crit_code",
                "type": "code_pin_mode",
                "expected": {"gpio": 18, "mode": "OUT"}
            }
        ]
    }
    
    proj = ProjectModel()
    proj.set_main_code("from machine import Pin\np = Pin(18, Pin.IN)") # Wrong mode
    
    sub = Submission(session_id="s1", activity_id="a1", snapshot=proj.to_dict())
    res_sub = eval_service.evaluate(sub, pedagogy_profile)
    
    assert res_sub.evaluation_result["status"] == "PARTIAL"
    assert res_sub.evaluation_result["criteria"]["crit_code"]["result"] == "FAIL"

def test_not_evaluated_unknown_type(eval_service):
    pedagogy_profile = {
        "criteria": [
            {
                "id": "crit_behavior",
                "type": "behavior_signal", # not handled directly by dummy rules mapping yet
                "blocking": False
            }
        ]
    }
    
    proj = ProjectModel()
    sub = Submission(session_id="s1", activity_id="a1", snapshot=proj.to_dict())
    res_sub = eval_service.evaluate(sub, pedagogy_profile)
    
    assert res_sub.evaluation_result["criteria"]["crit_behavior"]["result"] == "NOT_EVALUATED"

def test_empty_profile(eval_service):
    pedagogy_profile = {}
    proj = ProjectModel()
    sub = Submission(session_id="s1", activity_id="a1", snapshot=proj.to_dict())
    res_sub = eval_service.evaluate(sub, pedagogy_profile)
    
    assert res_sub.evaluation_result["status"] == "SUCCESS"
    assert res_sub.proposed_grade.percentage == 100.0
