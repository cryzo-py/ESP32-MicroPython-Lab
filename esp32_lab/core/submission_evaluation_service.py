# -*- coding: utf-8 -*-
from typing import Dict, Any, List
from .models.submission import Submission, ProposedGrade, SubmissionStatus
from .models.project import ProjectModel
from esp32_lab.application.education.evaluation.engine import EvaluationEngine
from esp32_lab.application.education.evaluation.models import EvaluationRule
from esp32_lab.core.courses import Lesson
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver

class DummyLesson(Lesson):
    def __init__(self, rules):
        self.id = "activity_lesson"
        self.chapter_num = 1
        self.chapter_title = "Activité"
        self.title = "Activité"
        self.summary = ""
        self.theory = ""
        self.challenge = ""
        self.required_components = []
        self.target_pin = None
        self.evaluation_rules = rules

class SubmissionEvaluationService:
    def __init__(self):
        self.engine = EvaluationEngine(net_resolver=None)

    def _build_resolver(self, project: ProjectModel) -> ElectricalNetResolver:
        # Note: Phase 6 tests used BreadboardTopology if any, but let's just add connections
        # if project topology is not explicitly needed. Actually let's just use connections.
        resolver = ElectricalNetResolver()
        for conn in project.connections:
            resolver.add_connection(
                conn.from_component, conn.from_pin,
                conn.to_component, conn.to_pin
            )
        return resolver

    def evaluate(self, submission: Submission, pedagogy_profile: Dict[str, Any]) -> Submission:
        if submission.status not in (SubmissionStatus.SUBMITTED, SubmissionStatus.AUTO_EVALUATED):
            return submission
            
        # 1. Recreate ProjectModel from snapshot
        project = ProjectModel.from_dict(submission.snapshot)
        
        # 2. Extract rules from SuccessProfile
        criteria = pedagogy_profile.get("criteria", [])
        rules = []
        for crit in criteria:
            if not crit.get("enabled", True):
                continue
                
            ctype = crit.get("type", "")
            rule_type = None
            gpio = None
            mode = None
            comp_type = None
            pin_name = None
            count = 1
            
            if ctype == "code_pin_mode":
                rule_type = "code_pin"
                gpio = crit.get("expected", {}).get("gpio")
                mode = crit.get("expected", {}).get("mode")
            elif ctype == "required_component":
                rule_type = "component"
                comp_type = crit.get("expected", {}).get("type")
                count = crit.get("expected", {}).get("count", 1)
            elif ctype == "electrical_path":
                rule_type = "topology"
                gpio = crit.get("expected", {}).get("gpio")
                comp_type = crit.get("expected", {}).get("component_type")
                pin_name = crit.get("expected", {}).get("pin_name")
            # map others...
            
            if rule_type:
                rule = EvaluationRule(
                    id=crit.get("id", ""),
                    type=rule_type,
                    required=crit.get("blocking", False),
                    weight=10, # default weight for auto-eval
                    gpio=gpio,
                    mode=mode,
                    component_type=comp_type,
                    count=count
                )
                rule.pin_name = pin_name
                rules.append(rule)
                
        lesson = DummyLesson(rules)
        
        # Prepare resolver
        resolver = self._build_resolver(project)
        self.engine.set_net_resolver(resolver)
        
        # 3. Evaluate
        items = self.engine.evaluate(lesson, project)
        
        # 4. Formulate Result
        eval_dict = {
            "status": "SUCCESS",
            "criteria": {}
        }
        
        total_score = 0
        total_max = 0
        all_passed = True
        
        for item in items:
            total_score += item.score
            total_max += item.max_score
            
            eval_dict["criteria"][item.id] = {
                "result": item.status,
                "message": item.pedagogical_message,
                "technical_reason": item.technical_message
            }
            if item.status == "FAIL":
                all_passed = False
                
        # Check criteria that were in SuccessProfile but couldn't be evaluated
        for crit in criteria:
            if not crit.get("enabled", True):
                continue
            cid = crit.get("id")
            if cid not in eval_dict["criteria"]:
                eval_dict["criteria"][cid] = {
                    "result": "NOT_EVALUATED",
                    "reason": "Moteur d'évaluation incapable d'analyser ce critère automatiquement."
                }
                if crit.get("blocking", False):
                    all_passed = False
                    
        eval_dict["status"] = "SUCCESS" if all_passed else "PARTIAL"
        
        submission.evaluation_result = eval_dict
        
        percentage = (total_score / total_max * 100) if total_max > 0 else 100.0
        submission.proposed_grade = ProposedGrade(
            score=total_score,
            max_score=total_max,
            percentage=percentage
        )
        
        submission.status = SubmissionStatus.WAITING_TEACHER
        return submission
