from typing import Dict, Any, List, Tuple

class ExerciseValidator:
    """Validates an exercise JSON representation to ensure data integrity before loading."""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        # Mandatory fields
        for field in ["id", "title", "mission", "evaluation_rules"]:
            if field not in data:
                errors.append(f"Champ obligatoire manquant : {field}")
                
        # Validate mission structure
        mission = data.get("mission")
        if mission:
            if not isinstance(mission, dict):
                errors.append("Le champ 'mission' doit être un objet JSON.")
            else:
                for subfield in ["context", "mission", "objective"]:
                    if subfield not in mission:
                        errors.append(f"Champ obligatoire de mission manquant : {subfield}")
                        
        # Validate rules
        rules = data.get("evaluation_rules")
        if rules and not isinstance(rules, list):
            errors.append("Le champ 'evaluation_rules' doit être une liste.")
            
        return len(errors) == 0, errors
