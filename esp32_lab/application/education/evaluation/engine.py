from typing import Dict, Any, List
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.courses import Lesson
from .models import EvaluationRule, EvaluationItem
from .code_structure_evaluator import CodeStructureEvaluator
from .component_evaluator import ComponentEvaluator
from .topology_evaluator import TopologyEvaluator

class EvaluationEngine:
    def __init__(self, net_resolver=None):
        self.code_evaluator = CodeStructureEvaluator()
        self.component_evaluator = ComponentEvaluator()
        self.topology_evaluator = TopologyEvaluator()
        self.net_resolver = net_resolver
        
    def set_net_resolver(self, resolver):
        self.net_resolver = resolver
        
    def evaluate(self, lesson: Lesson, project: ProjectModel) -> List[EvaluationItem]:
        items = []
        code = project.get_main_code()
        
        # 1. Parse Code
        ast_result = self.code_evaluator.evaluate(code)
        
        # Backward compatibility for old lessons
        # Instead of completely breaking old `Lesson` logic, we can map some dynamically.
        # But for new lessons with `evaluation_rules`, we use them.
        
        rules = getattr(lesson, "evaluation_rules", [])
        
        if not rules:
            return self._legacy_evaluate(lesson, project, ast_result)
            
        for rule in rules:
            if rule.type == "code_pin":
                # find if pin exists in ast_result["pins"]
                found = False
                for p in ast_result["pins"]:
                    if p["gpio"] == rule.gpio and (rule.mode is None or p["mode"] == rule.mode):
                        found = True
                        break
                
                if found:
                    items.append(EvaluationItem(
                        id=rule.id, category="CODE", status="PASS",
                        score=rule.weight, max_score=rule.weight,
                        message=f"Le GPIO {rule.gpio} est correctement configuré.",
                        technical_message=f"AST trouvé pour Pin({rule.gpio}, {rule.mode})",
                        pedagogical_message="Votre code déclare bien la broche requise avec le bon mode."
                    ))
                else:
                    items.append(EvaluationItem(
                        id=rule.id, category="CODE", status="FAIL",
                        score=0, max_score=rule.weight,
                        message=f"Le GPIO {rule.gpio} n'est pas configuré en {rule.mode}.",
                        technical_message="AST Pin() node manquant.",
                        pedagogical_message="Vérifiez la déclaration de votre broche. Utilisez Pin(numero, mode)."
                    ))
            
            elif rule.type == "component":
                # Evaluate component
                req = [rule.component_type] * (rule.count or 1)
                comp_result = self.component_evaluator.evaluate(project, req)
                if comp_result["all_found"]:
                    items.append(EvaluationItem(
                        id=rule.id, category="PHYSICAL", status="PASS",
                        score=rule.weight, max_score=rule.weight,
                        message=f"Composant {rule.component_type} présent.",
                        technical_message="Found in project.components",
                        pedagogical_message="Les composants requis sont bien placés sur l'espace de travail."
                    ))
                else:
                    items.append(EvaluationItem(
                        id=rule.id, category="PHYSICAL", status="FAIL",
                        score=0, max_score=rule.weight,
                        message=f"Il manque le composant : {rule.component_type}.",
                        technical_message="Not found in project.components",
                        pedagogical_message="Glissez les composants requis depuis la palette."
                    ))
                    
            elif rule.type == "topology":
                # Evaluate topology using the resolver
                if self.net_resolver:
                    top_result = self.topology_evaluator.evaluate_project(project, self.net_resolver, [rule])
                    for tr in top_result:
                        if tr["connected"]:
                            items.append(EvaluationItem(
                                id=rule.id, category="PHYSICAL", status="PASS",
                                score=rule.weight, max_score=rule.weight,
                                message=tr["message"],
                                technical_message="Resolver confirmed electrical path.",
                                pedagogical_message="Le signal arrive bien au bon composant."
                            ))
                        else:
                            items.append(EvaluationItem(
                                id=rule.id, category="PHYSICAL", status="FAIL",
                                score=0, max_score=rule.weight,
                                message=tr["message"],
                                technical_message="Resolver found no electrical path.",
                                pedagogical_message="Vérifiez que : 1. les pins sont bien insérés dans la breadboard. 2. les jumpers relient les bonnes colonnes."
                            ))
                else:
                    items.append(EvaluationItem(
                        id=rule.id, category="PHYSICAL", status="NOT_APPLICABLE",
                        score=0, max_score=rule.weight,
                        message="Moteur de résolution inactif.",
                        technical_message="net_resolver is None",
                        pedagogical_message=""
                    ))
                    
        return items
        
    def _legacy_evaluate(self, lesson: Lesson, project: ProjectModel, ast_result: Dict[str, Any]) -> List[EvaluationItem]:
        # Adapter mapping old hardcoded evaluations to new EvaluationItem format
        return []
