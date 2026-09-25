# -*- coding: utf-8 -*-
import pytest
from esp32_lab.core.models.success_profile import SuccessProfileValidator, ensure_valid_profile

def test_empty_profile_valid():
    assert SuccessProfileValidator.validate({}) == []
    assert SuccessProfileValidator.validate({"criteria": []}) == []

def test_creation_topology():
    crit = {
        "id": "topo_1", "category": "topology", "type": "required_connection",
        "description": "Led to PWM", "enabled": True, "blocking": True,
        "target": {"kind": "gpio_capability", "capability": "PWM"}
    }
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []

def test_creation_code():
    crit = {
        "id": "code_1", "category": "code", "type": "required_api",
        "description": "Must use PWM", "enabled": True, "blocking": False
    }
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []

def test_creation_behavior():
    crit = {
        "id": "behav_1", "category": "behavior", "type": "causality_mapping",
        "description": "Pot varies LED", "enabled": True, "blocking": True,
        "trigger": {"component": "pot"}, "expect": {"component": "led"}
    }
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []

def test_creation_constraint():
    crit = {
        "id": "const_1", "category": "constraints", "type": "allowed_range",
        "description": "Resistor value", "enabled": True, "blocking": True,
        "min": 220, "max": 1000
    }
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []

def test_validation_category():
    crit = {
        "id": "bad_1", "category": "magic", "type": "spell",
        "description": "Cast spell", "enabled": True, "blocking": True
    }
    errs = SuccessProfileValidator.validate({"criteria": [crit]})
    assert len(errs) > 0
    assert any("catégorie inconnue" in e for e in errs)

def test_validation_type():
    crit = {
        "id": "bad_2", "category": "topology", "type": "causality_mapping",
        "description": "Wrong type", "enabled": True, "blocking": True
    }
    errs = SuccessProfileValidator.validate({"criteria": [crit]})
    assert len(errs) > 0
    assert any("invalide pour la catégorie" in e for e in errs)

def test_validation_structure():
    crit = {
        "id": "bad_3", "category": "topology", "type": "required_connection",
        "description": "Missing target", "enabled": True, "blocking": True
    }
    errs = SuccessProfileValidator.validate({"criteria": [crit]})
    assert len(errs) > 0
    assert any("exige un champ 'target'" in e for e in errs)

def test_blocking_vs_severity():
    # Valid criterion with blocking but no severity
    crit = {
        "id": "c_1", "category": "code", "type": "required_api",
        "description": "No severity", "enabled": True, "blocking": False
    }
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []

def test_enabled_independent_of_blocking():
    crit = {
        "id": "c_1", "category": "code", "type": "required_api",
        "description": "Test", "enabled": False, "blocking": True
    }
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []

def test_depends_on():
    crit = {
        "id": "c_1", "category": "code", "type": "required_api",
        "description": "Test", "enabled": True, "blocking": True,
        "depends_on": ["topo_1"]
    }
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []
    
    crit_bad = crit.copy()
    crit_bad["depends_on"] = "topo_1"
    assert len(SuccessProfileValidator.validate({"criteria": [crit_bad]})) > 0

def test_causality_mapping_missing_expect():
    crit = {
        "id": "behav_1", "category": "behavior", "type": "causality_mapping",
        "description": "Pot varies LED", "enabled": True, "blocking": True,
        "trigger": {"component": "pot"}
    }
    assert len(SuccessProfileValidator.validate({"criteria": [crit]})) > 0

def test_invalid_behavior_criterion():
    crit = {
        "id": "behav_1", "category": "behavior"
        # missing type, desc
    }
    errs = SuccessProfileValidator.validate({"criteria": [crit]})
    assert len(errs) >= 2

def test_backward_compatibility_old_lab32():
    # Should not raise exception
    ensure_valid_profile(None)
    ensure_valid_profile({})
    ensure_valid_profile({"locked_elements": {}})

def test_serialization():
    # Serialization is just json.dumps which natively works on valid dictionaries.
    # Here we just verify dict forms are valid
    import json
    profile = {"criteria": [{"id": "t", "category": "topology", "type": "required_component", "description": "d", "enabled": True, "blocking": True}]}
    s = json.dumps(profile)
    assert "required_component" in s

def test_deserialization():
    import json
    s = '{"criteria": [{"id": "t", "category": "topology", "type": "required_component", "description": "d", "enabled": true, "blocking": true}]}'
    profile = json.loads(s)
    assert SuccessProfileValidator.validate(profile) == []

def test_stable_ids():
    crit = {"id": "my_stable_id_123", "category": "topology", "type": "required_component", "description": "d", "enabled": True, "blocking": True}
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []

def test_alternative_compatible_solution():
    crit = {
        "id": "t1", "category": "topology", "type": "pin_capability",
        "description": "Any PWM pin", "enabled": True, "blocking": True,
        "capability": "PWM"
    }
    assert SuccessProfileValidator.validate({"criteria": [crit]}) == []

def test_no_python_execution():
    crit = {
        "id": "t1", "category": "topology", "type": "pin_capability",
        "description": "Any PWM pin", "enabled": True, "blocking": True,
        "eval": "eval('__import__(\"os\").system(\"echo bad\")')"
    }
    errs = SuccessProfileValidator.validate({"criteria": [crit]})
    assert len(errs) > 0
    assert any("exécution Python" in e for e in errs)
    
    crit2 = {
        "id": "t2", "category": "topology", "type": "pin_capability",
        "description": "lambda: True", "enabled": True, "blocking": True
    }
    errs2 = SuccessProfileValidator.validate({"criteria": [crit2]})
    assert len(errs2) > 0
