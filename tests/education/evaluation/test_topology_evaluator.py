import pytest
from esp32_lab.application.education.evaluation.topology_evaluator import TopologyEvaluator
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.component import ComponentModel
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.application.education.evaluation.models import EvaluationRule

def test_topology_valid_path():
    proj = ProjectModel()
    proj.components.append(ComponentModel(id="led_1", type="led"))
    
    resolver = ElectricalNetResolver()
    # Mocking connection ESP32 GPIO2 -> LED Anode
    resolver.connections = [(("esp32", "GPIO2"), ("led_1", "anode"))]
    
    evaluator = TopologyEvaluator()
    rule = EvaluationRule(id="rule1", type="topology", gpio=2, component_type="led", pin_name="anode")
    
    res = evaluator.evaluate_project(proj, resolver, [rule])
    assert len(res) == 1
    assert res[0]["status"] == "PASS"
    assert res[0]["connected"] is True

def test_topology_invalid_path():
    proj = ProjectModel()
    proj.components.append(ComponentModel(id="led_1", type="led"))
    
    resolver = ElectricalNetResolver()
    # GPIO4 connected, but rule wants GPIO2
    resolver.connections = [(("esp32", "GPIO4"), ("led_1", "anode"))]
    
    evaluator = TopologyEvaluator()
    rule = EvaluationRule(id="rule1", type="topology", gpio=2, component_type="led", pin_name="anode")
    
    res = evaluator.evaluate_project(proj, resolver, [rule])
    assert res[0]["status"] == "FAIL"
    assert res[0]["connected"] is False

def test_topology_missing_component():
    proj = ProjectModel()
    resolver = ElectricalNetResolver()
    
    evaluator = TopologyEvaluator()
    rule = EvaluationRule(id="rule1", type="topology", gpio=2, component_type="led", pin_name="anode")
    
    res = evaluator.evaluate_project(proj, resolver, [rule])
    assert res[0]["status"] == "FAIL"
    assert "manquant" in res[0]["message"]
