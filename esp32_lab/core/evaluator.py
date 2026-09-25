"""
Moteur d'évaluation automatique des exercices et TPs pour ESP32 MicroPython Lab
Analyse statique du code (AST), vérification des composants du circuit et de leur câblage.
(Version Hardened - Phase 6.0-B)
"""

import ast
from dataclasses import dataclass, field
from .courses import Lesson
from .models.project import ProjectModel
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.application.education.evaluation.code_structure_evaluator import CodeStructureEvaluator

@dataclass
class EvaluationCriterion:
    id: str
    title: str
    description: str
    points: int
    max_points: int
    passed: bool
    feedback: str

@dataclass
class EvaluationResult:
    lesson_id: str
    lesson_title: str
    score: int
    max_score: int
    passed: bool
    criteria: list[EvaluationCriterion]
    general_feedback: str

    @property
    def percentage(self) -> int:
        return int((self.score / self.max_score) * 100) if self.max_score > 0 else 0

class ExerciseEvaluator:
    """Évaluateur automatique de projets pour les leçons pédagogiques."""
    
    def __init__(self, net_resolver: ElectricalNetResolver = None):
        self.net_resolver = net_resolver
        self.code_evaluator = CodeStructureEvaluator()

    def evaluate(self, lesson: Lesson, project: ProjectModel) -> EvaluationResult:
        criteria: list[EvaluationCriterion] = []
        code = project.get_main_code()
        
        # Ast analysis
        ast_result = self.code_evaluator.evaluate(code)
        syntax_ok = True
        try:
            ast.parse(code)
        except SyntaxError:
            syntax_ok = False

        # 1. Syntaxe du code (25 pts)
        c_syntax = self._check_syntax(code, syntax_ok)
        criteria.append(c_syntax)

        # 2. Imports requis (20 pts)
        c_imports = self._check_imports(lesson, code, ast_result, syntax_ok)
        criteria.append(c_imports)

        # 3. Présence des composants requis (25 pts)
        c_components = self._check_components(lesson, project)
        criteria.append(c_components)

        # 4. Câblage et connexions (20 pts)
        c_wiring = self._check_wiring(lesson, project)
        criteria.append(c_wiring)

        # 5. Logique et configuration (10 pts)
        c_logic = self._check_logic(lesson, code, ast_result, syntax_ok)
        criteria.append(c_logic)

        total_score = sum(c.points for c in criteria)
        max_score = sum(c.max_points for c in criteria)
        passed = all(c.passed for c in criteria)

        general_feedback = "🎉 Excellent travail ! Vous avez rempli tous les critères de cet exercice." if passed else "🛠️ Il reste quelques points à corriger. Consultez le détail ci-dessus."

        return EvaluationResult(
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            score=total_score,
            max_score=max_score,
            passed=passed,
            criteria=criteria,
            general_feedback=general_feedback
        )

    def _check_syntax(self, code: str, syntax_ok: bool) -> EvaluationCriterion:
        if syntax_ok:
            return EvaluationCriterion("syntax", "Syntaxe Python", "Le code doit être valide.", 25, 25, True, "✅ Le code est syntaxiquement correct.")
        return EvaluationCriterion("syntax", "Syntaxe Python", "Le code doit être valide.", 0, 25, False, "❌ Erreur de syntaxe détectée dans votre code MicroPython.")

    def _check_imports(self, lesson: Lesson, code: str, ast_result: dict, syntax_ok: bool) -> EvaluationCriterion:
        if not syntax_ok:
            return EvaluationCriterion("imports", "Bibliothèques MicroPython", "Importation des modules requis.", 0, 20, False, "Impossible de vérifier les imports (erreur de syntaxe).")

        expected_needs = []
        if lesson.id in ("lesson_1_gpio_led", "lesson_2_button", "lesson_9_relay", "lesson_10_neopixel"):
            expected_needs.append("Pin")
        if lesson.id in ("lesson_3_pot_adc", "lesson_4_servo_pwm"):
            expected_needs.append("PWM")
        if lesson.id == "lesson_3_pot_adc":
            expected_needs.append("ADC")
        if lesson.id in ("lesson_6_oled", "lesson_8_lcd"):
            expected_needs.append("I2C")
        
        imported_names = []
        for imp in ast_result["imports"]:
            if imp["name"]:
                imported_names.append(imp["name"])
            else:
                imported_names.append(imp["module"])

        missing = [need for need in expected_needs if need not in imported_names and need not in ast_result.get("imports", [])]
        
        if not missing:
            return EvaluationCriterion("imports", "Bibliothèques MicroPython", "Importation des modules requis.", 20, 20, True, "✅ Toutes les bibliothèques requises sont importées.")
        
        return EvaluationCriterion("imports", "Bibliothèques MicroPython", "Importation des modules requis.", 0, 20, False, f"❌ Module/Classe manquant(e) : {', '.join(missing)}.")

    def _check_components(self, lesson: Lesson, project: ProjectModel) -> EvaluationCriterion:
        req_types = lesson.required_components
        if not req_types:
            return EvaluationCriterion("components", "Composants du circuit", "Présence des composants.", 25, 25, True, "✅ Aucun composant spécifique requis.")

        existing_types = [c.type.lower() for c in project.components]
        missing = [rt for rt in req_types if rt.lower() not in existing_types]

        if not missing:
            return EvaluationCriterion("components", "Composants du circuit", f"Présence de : {', '.join(req_types)}.", 25, 25, True, f"✅ Tous les composants requis sont placés.")
        
        found_count = len(req_types) - len(missing)
        pts = int((found_count / len(req_types)) * 25)
        return EvaluationCriterion("components", "Composants du circuit", f"Présence de : {', '.join(req_types)}.", pts, 25, False, f"❌ Composant(s) manquant(s) : {', '.join(missing)}.")

    def _check_wiring(self, lesson: Lesson, project: ProjectModel) -> EvaluationCriterion:
        if not lesson.required_components and lesson.target_pin is None:
            return EvaluationCriterion("wiring", "Câblage électrique", "Connexions matérielles.", 20, 20, True, "✅ Aucun câblage externe requis.")
            
        if not self.net_resolver:
            # Fallback legacy string match
            if lesson.target_pin is not None:
                target_str = f"gpio{lesson.target_pin}"
                num_str = str(lesson.target_pin)
                target_found = False

                for conn in project.connections:
                    f_p = conn.from_pin.lower()
                    t_p = conn.to_pin.lower()
                    if (target_str in f_p or f_p == num_str or
                        target_str in t_p or t_p == num_str):
                        target_found = True
                        break

                if target_found:
                    return EvaluationCriterion("wiring", "Câblage électrique", f"Raccordement sur GPIO {lesson.target_pin}.", 20, 20, True, f"✅ Connexion électrique valide détectée sur GPIO {lesson.target_pin}.")
                else:
                    return EvaluationCriterion("wiring", "Câblage électrique", f"Raccordement sur GPIO {lesson.target_pin}.", 0, 20, False, f"❌ Aucun fil n'est connecté au GPIO {lesson.target_pin}.")
            return EvaluationCriterion("wiring", "Câblage électrique", "Connexions électriques.", 20, 20, True, "✅ Câblage présent.")
            
        # Hardened Topology Check
        resolver = self.net_resolver
        if lesson.target_pin is not None:
            source_comp = "esp32"
            source_pin = f"GPIO{lesson.target_pin}"
            
            target_found = False
            
            # Find destination component
            for comp in project.components:
                if comp.type.lower() in [r.lower() for r in lesson.required_components]:
                    # Need to check if there is an electrical path to ANY pin of this component
                    # We query the electrical net graph
                    net_pins = resolver.get_connected_pins(source_comp, source_pin)
                    for (c_id, p_id) in net_pins:
                        if c_id == comp.id:
                            target_found = True
                            break
                    if target_found:
                        break
                        
            if target_found:
                return EvaluationCriterion("wiring", "Câblage électrique", f"Raccordement sur GPIO {lesson.target_pin}.", 20, 20, True, f"✅ Connexion électrique valide détectée sur GPIO {lesson.target_pin}.")
            else:
                return EvaluationCriterion("wiring", "Câblage électrique", f"Raccordement sur GPIO {lesson.target_pin}.", 0, 20, False, f"❌ Aucun chemin électrique valide entre GPIO {lesson.target_pin} et le composant cible.")

        return EvaluationCriterion("wiring", "Câblage électrique", "Connexions électriques.", 20, 20, True, "✅ Câblage présent.")

    def _check_logic(self, lesson: Lesson, code: str, ast_result: dict, syntax_ok: bool) -> EvaluationCriterion:
        if not syntax_ok:
            return EvaluationCriterion("logic", "Logique et configuration", "Configuration des broches.", 0, 10, False, "❌ Logique non évaluable (erreur de syntaxe).")

        if lesson.target_pin is not None:
            pin_found = False
            for p in ast_result["pins"]:
                if p["gpio"] == lesson.target_pin:
                    pin_found = True
                    break
            for p in ast_result["pwm"]:
                if p["gpio"] == lesson.target_pin:
                    pin_found = True
                    break
            for p in ast_result["adc"]:
                if p["gpio"] == lesson.target_pin:
                    pin_found = True
                    break
                    
            if pin_found:
                return EvaluationCriterion("logic", "Logique et configuration", f"Configuration de GPIO {lesson.target_pin}.", 10, 10, True, f"✅ Le GPIO {lesson.target_pin} est correctement configuré via AST.")
            else:
                return EvaluationCriterion("logic", "Logique et configuration", f"Configuration de GPIO {lesson.target_pin}.", 0, 10, False, f"❌ Le GPIO {lesson.target_pin} n'est pas correctement initialisé dans le code (ex: `Pin({lesson.target_pin}, Pin.OUT)`).")

        return EvaluationCriterion("logic", "Logique et configuration", "Configuration.", 10, 10, True, "✅ Configuration validée.")
