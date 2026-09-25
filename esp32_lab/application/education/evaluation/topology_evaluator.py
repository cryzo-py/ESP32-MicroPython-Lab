from typing import Dict, Any, List, Optional
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.breadboard_topology import BreadboardTopology

class TopologyEvaluator:
    """Evaluates the electrical connectivity using the single source of truth (ElectricalNetResolver)."""
    
    def evaluate_path(self, resolver: ElectricalNetResolver, source_comp: str, source_pin: str, dest_comp: str, dest_pin: str) -> Dict[str, Any]:
        """Checks if a valid electrical path exists between two pins."""
        is_connected = resolver.are_connected(source_comp, source_pin, dest_comp, dest_pin)
        
        return {
            "connected": is_connected,
            "source": f"{source_comp}.{source_pin}",
            "dest": f"{dest_comp}.{dest_pin}",
            "floating": not is_connected
        }

    def evaluate_project(self, project: ProjectModel, resolver: ElectricalNetResolver, rules: List[Any]) -> List[Dict[str, Any]]:
        results = []
        # Fallback mechanism if no resolver is passed
        for rule in rules:
            if rule.type == "topology":
                # Find components by type
                source_comp = "esp32"
                source_pin = f"GPIO{rule.gpio}"
                
                # Find dest comp ID
                dest_id = None
                for c in project.components:
                    if c.type.lower() == rule.component_type.lower():
                        dest_id = c.id
                        break
                        
                if not dest_id:
                    results.append({
                        "rule_id": rule.id,
                        "status": "FAIL",
                        "message": f"Composant {rule.component_type} manquant.",
                        "connected": False
                    })
                    continue
                    
                path_info = self.evaluate_path(resolver, source_comp, source_pin, dest_id, rule.pin_name)
                
                if path_info["connected"]:
                    results.append({
                        "rule_id": rule.id,
                        "status": "PASS",
                        "message": f"La broche {source_pin} est correctement reliée au {rule.component_type} ({rule.pin_name}).",
                        "connected": True
                    })
                else:
                    results.append({
                        "rule_id": rule.id,
                        "status": "FAIL",
                        "message": f"Aucun chemin électrique valide ne relie {source_pin} à {rule.component_type} ({rule.pin_name}).",
                        "connected": False
                    })
        return results
