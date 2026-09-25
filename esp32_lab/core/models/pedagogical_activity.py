# -*- coding: utf-8 -*-
import uuid
from enum import Enum

class ActivityType(str, Enum):
    TP = "tp"
    EXERCISE = "exercise"
    EXAM = "exam"

def get_default_settings(activity_type: str) -> dict:
    if activity_type == ActivityType.EXAM:
        return {
            "allow_hints": False,
            "allow_feedback": False,
            "strict_mode": True,
            "attempts_allowed": 1,
            "auto_submit": True
        }
    elif activity_type == ActivityType.EXERCISE:
        return {
            "allow_hints": True,
            "allow_feedback": True,
            "strict_mode": False,
            "attempts_allowed": None,
            "auto_submit": False
        }
    else:  # TP
        return {
            "allow_hints": True,
            "allow_feedback": True,
            "strict_mode": False,
            "attempts_allowed": None,
            "auto_submit": False
        }

def create_default_activity(act_type: str = ActivityType.TP) -> dict:
    return {
        "id": f"act_{str(uuid.uuid4())[:8]}",
        "type": act_type,
        "title": "Nouvelle Activité",
        "duration_minutes": 0,  # 0 means unlimited
        "settings": get_default_settings(act_type)
    }

class ActivityContext:
    """Wrapper to interact safely with the pedagogy_profile's activity data."""
    def __init__(self, pedagogy_profile: dict = None):
        self.profile = pedagogy_profile

    @property
    def has_activity(self) -> bool:
        return bool(self.profile and "activity" in self.profile)

    @property
    def activity(self) -> dict | None:
        if not self.profile:
            return None
        act = self.profile.get("activity")
        if act and not act.get("id"):
            import uuid
            act["id"] = f"act_{str(uuid.uuid4())[:8]}"
        return act
        
    @property
    def activity_type(self) -> str:
        act = self.activity
        return act.get("type", ActivityType.TP) if act else ""
