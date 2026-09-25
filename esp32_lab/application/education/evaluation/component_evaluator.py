from typing import List, Dict, Any
from esp32_lab.core.models.project import ProjectModel

class ComponentEvaluator:
    """Evaluates the presence and basic parameters of components in the project."""
    
    def evaluate(self, project: ProjectModel, required_components: List[str]) -> Dict[str, Any]:
        existing_types = [c.type.lower() for c in project.components if c.type != "breadboard" and c.type not in ("esp32", "board")]
        
        missing = []
        found = []
        
        for req in required_components:
            req_lower = req.lower()
            if req_lower in existing_types:
                found.append(req_lower)
                existing_types.remove(req_lower)
            else:
                missing.append(req_lower)
                
        # Also check for pins inserted
        # A component is technically present if it is in project.components
        # For Level 5/6 we can check if it is inside topology.occupants
        
        return {
            "found": found,
            "missing": missing,
            "extra": existing_types,
            "all_found": len(missing) == 0
        }
