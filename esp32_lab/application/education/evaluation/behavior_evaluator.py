from typing import Dict, Any, List

class BehaviorEvaluator:
    """Interface for evaluating runtime behavior of the simulation."""
    
    def evaluate(self, simulation_engine, rules: List[Any]) -> List[Dict[str, Any]]:
        # In the future, this can hook into SimulationEngine to observe state
        results = []
        for rule in rules:
            if rule.type == "behavior":
                # Concept placeholder
                results.append({
                    "rule_id": rule.id,
                    "status": "NOT_APPLICABLE",
                    "message": "Evaluation comportementale non implémentée.",
                })
        return results
