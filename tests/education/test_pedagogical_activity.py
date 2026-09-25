# -*- coding: utf-8 -*-
import pytest
from esp32_lab.core.models.pedagogical_activity import ActivityType, get_default_settings, create_default_activity, ActivityContext

def test_creation_tp():
    act = create_default_activity(ActivityType.TP)
    assert act["type"] == ActivityType.TP
    assert act["duration_minutes"] == 0

def test_creation_exercise():
    act = create_default_activity(ActivityType.EXERCISE)
    assert act["type"] == ActivityType.EXERCISE
    assert act["settings"]["allow_hints"] is True

def test_creation_exam():
    act = create_default_activity(ActivityType.EXAM)
    assert act["type"] == ActivityType.EXAM
    assert act["settings"]["strict_mode"] is True
    assert act["settings"]["allow_hints"] is False

def test_invalid_type():
    # Enums are strict if parsed, but if just strings, we handle it as fallback.
    act = create_default_activity("magic")
    assert act["type"] == "magic"
    assert "strict_mode" in act["settings"] # falls back to TP defaults

def test_serialization():
    import json
    act = create_default_activity(ActivityType.TP)
    s = json.dumps(act)
    assert "tp" in s

def test_deserialization():
    import json
    s = '{"type": "exam", "duration_minutes": 90, "settings": {"strict_mode": true}}'
    act = json.loads(s)
    assert act["type"] == "exam"
    assert act["duration_minutes"] == 90
    assert act["settings"]["strict_mode"] is True

def test_duration_minutes_valid():
    act = create_default_activity(ActivityType.TP)
    act["duration_minutes"] = 45
    assert act["duration_minutes"] == 45

def test_activity_without_duration():
    act = create_default_activity(ActivityType.TP)
    assert act["duration_minutes"] == 0

def test_default_settings_tp():
    s = get_default_settings(ActivityType.TP)
    assert s["allow_hints"] is True
    assert s["strict_mode"] is False

def test_default_settings_exercise():
    s = get_default_settings(ActivityType.EXERCISE)
    assert s["allow_hints"] is True
    assert s["strict_mode"] is False

def test_default_settings_exam():
    s = get_default_settings(ActivityType.EXAM)
    assert s["allow_hints"] is False
    assert s["strict_mode"] is True

def test_normal_project_no_activity():
    ctx = ActivityContext(None)
    assert ctx.has_activity is False
    assert ctx.activity is None
    
    ctx2 = ActivityContext({"mission": {}})
    assert ctx2.has_activity is False

def test_backward_compatibility_lab32():
    # old profile without activity section
    profile = {"locked_elements": {}}
    ctx = ActivityContext(profile)
    assert ctx.has_activity is False

def test_mission_reused():
    profile = {"mission": {"title": "Test"}, "activity": create_default_activity()}
    ctx = ActivityContext(profile)
    assert ctx.has_activity is True

def test_success_profile_reused():
    profile = {"criteria": [{"type": "required_component"}], "activity": create_default_activity()}
    ctx = ActivityContext(profile)
    assert ctx.has_activity is True

def test_locked_elements_reused():
    profile = {"locked_elements": {"components": []}, "activity": create_default_activity()}
    ctx = ActivityContext(profile)
    assert ctx.has_activity is True

def test_no_python_execution_in_activity_config():
    act = create_default_activity(ActivityType.TP)
    import re
    assert not re.search(r"lambda\s*:", str(act))
