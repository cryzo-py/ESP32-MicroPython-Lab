import os
import json
import sys

# Ajouter le chemin racine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from esp32_lab.core.courses import get_course_curriculum
from esp32_lab.application.education.exercises.models import Exercise, ExerciseMission, LearningObjective, Prerequisite
from esp32_lab.application.education.exercises.validator import ExerciseValidator

def main():
    lessons = get_course_curriculum()
    print(f"Trouvé {len(lessons)} lessons dans courses.py")
    
    inventory_md = "# INVENTAIRE DES COURS LEGACY\n\n"
    mapping_md = "# MAPPING LEGACY -> EXERCISES\n\n| Legacy ID | Exercise ID | Status | Reason |\n|---|---|---|---|\n"
    
    # Supported components in current hardware simulation core
    supported_components = ["led", "resistor", "button", "potentiometer", "servo", "bme280", "ssd1306", "w25qxx"]
    
    os.makedirs("esp32_lab/application/education/exercises/data", exist_ok=True)
    os.makedirs("docs/education", exist_ok=True)
    
    migrated_count = 0
    manual_review_count = 0
    not_applicable_count = 0
    
    for l in lessons:
        inventory_md += f"## {l.id} : {l.title}\n"
        inventory_md += f"- **Chapter** : {l.chapter_num} ({l.chapter_title})\n"
        inventory_md += f"- **Target Pin** : {l.target_pin}\n"
        inventory_md += f"- **Components** : {', '.join(l.required_components)}\n\n"
        
        # Determine if we can migrate it
        can_migrate = True
        reason = ""
        for comp in l.required_components:
            if comp == "oled": comp = "ssd1306"
            if comp not in supported_components and comp not in ["dht11", "lcd", "relay", "neopixel", "hcsr04", "dht22"]:
                can_migrate = False
                reason = f"Unsupported component: {comp}"
        
        # Known legacy unsupported components
        unsupported = {"dht11", "lcd", "relay", "neopixel", "hcsr04", "dht22"}
        if any(c in unsupported for c in l.required_components):
            can_migrate = False
            reason = "Component not simulated by frozen Core Hardware"
            
        if l.id == "lesson_11_wifi":
            can_migrate = False
            reason = "Network/Wi-Fi is mocked but not part of Physical evaluation scope"
            
        exercise_id = l.id.replace("lesson_", "ex_")
        
        if can_migrate:
            # We migrate this to JSON!
            mission = {
                "context": l.summary,
                "mission": l.challenge,
                "objective": f"Terminer le {l.title}",
                "constraints": []
            }
            
            # Create evaluation rules based on legacy fields
            rules = []
            if l.target_pin is not None:
                rules.append({
                    "id": "rule_code_pin",
                    "type": "code_pin",
                    "gpio": l.target_pin,
                    "mode": "OUT" if "led" in l.required_components else "IN",
                    "weight": 50
                })
                
                if l.required_components:
                    comp_type = l.required_components[0]
                    rules.append({
                        "id": "rule_topology",
                        "type": "topology",
                        "gpio": l.target_pin,
                        "component_type": comp_type,
                        "weight": 50
                    })
                    
            skills = []
            if "led" in l.required_components: skills.append("GPIO")
            if "button" in l.required_components: skills.append("GPIO")
            if "potentiometer" in l.required_components: skills.append("ADC")
            if "pwm" in l.id: skills.append("PWM")
            if "servo" in l.id: skills.append("SERVO")
            if "i2c" in l.id or "oled" in l.id: skills.append("I2C")
            
            ex_data = {
                "id": exercise_id,
                "title": l.title,
                "summary": l.summary,
                "mission": mission,
                "difficulty": "BEGINNER" if l.chapter_num < 4 else "INTERMEDIATE",
                "skills": skills,
                "evaluation_rules": rules,
                "hints": [
                    "Vérifiez le câblage sur la platine.",
                    "Avez-vous bien déclaré les numéros de broches dans le code ?"
                ]
            }
            
            # Starter project dict representation
            if l.starter_project:
                ex_data["starter_project"] = l.starter_project.to_dict()
                
            # Validate
            is_valid, errors = ExerciseValidator.validate(ex_data)
            if is_valid:
                with open(f"esp32_lab/application/education/exercises/data/{exercise_id}.json", "w", encoding="utf-8") as f:
                    json.dump(ex_data, f, indent=2, ensure_ascii=False)
                
                mapping_md += f"| {l.id} | {exercise_id} | MIGRATED | OK |\n"
                migrated_count += 1
            else:
                mapping_md += f"| {l.id} | {exercise_id} | REQUIRES_MANUAL_REVIEW | Validation errors: {errors} |\n"
                manual_review_count += 1
        else:
            mapping_md += f"| {l.id} | N/A | NOT_APPLICABLE | {reason} |\n"
            not_applicable_count += 1
            
    with open("docs/education/PHASE_6.0_E_INVENTORY.md", "w", encoding="utf-8") as f:
        f.write(inventory_md)
        
    with open("docs/education/CURRICULUM_MAPPING.md", "w", encoding="utf-8") as f:
        f.write(mapping_md)
        
    print(f"Migrated: {migrated_count}")
    print(f"Requires Manual Review: {manual_review_count}")
    print(f"Not Applicable: {not_applicable_count}")

if __name__ == "__main__":
    main()
