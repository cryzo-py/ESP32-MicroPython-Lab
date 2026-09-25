import pytest
from esp32_lab.application.education.evaluation.component_evaluator import ComponentEvaluator
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.component import ComponentModel

def test_component_presence():
    proj = ProjectModel()
    proj.components.append(ComponentModel(id="led_1", type="led"))
    proj.components.append(ComponentModel(id="resistor_1", type="resistor"))
    
    evaluator = ComponentEvaluator()
    res = evaluator.evaluate(proj, ["led", "resistor"])
    
    assert res["all_found"] is True
    assert "led" in res["found"]
    assert "resistor" in res["found"]
    assert len(res["missing"]) == 0

def test_component_missing():
    proj = ProjectModel()
    proj.components.append(ComponentModel(id="led_1", type="led"))
    
    evaluator = ComponentEvaluator()
    res = evaluator.evaluate(proj, ["led", "resistor"])
    
    assert res["all_found"] is False
    assert "led" in res["found"]
    assert "resistor" in res["missing"]

def test_component_multiple():
    proj = ProjectModel()
    proj.components.append(ComponentModel(id="led_1", type="led"))
    proj.components.append(ComponentModel(id="led_2", type="led"))
    
    evaluator = ComponentEvaluator()
    res = evaluator.evaluate(proj, ["led", "led"])
    
    assert res["all_found"] is True
    assert len(res["found"]) == 2
