import json
import os
from typing import Dict, Any, List

class HintEngine:
    def __init__(self, lang: str = "fr"):
        self.lang = lang
        self.i18n_data = self._load_i18n()
        self.hint_cost_policy = 0 # Configurable cost per hint

    def _load_i18n(self) -> Dict[str, Any]:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        i18n_path = os.path.join(base_dir, "i18n", f"{self.lang}.json")
        try:
            with open(i18n_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_hints_for_rule(self, rule_type: str, rule_params: Dict[str, Any]) -> List[str]:
        # Mapping simple rule types to i18n keys
        i18n_key = "DEFAULT"
        if rule_type == "topology":
            i18n_key = "TOPOLOGY_MISSING_PATH"
        elif rule_type == "code_pin":
            i18n_key = "CODE_MISSING_PIN_CONFIG"
        elif rule_type == "component":
            i18n_key = "TOPOLOGY_MISSING_COMPONENT"
            
        data = self.i18n_data.get(i18n_key, {})
        
        hints = []
        for i in range(1, 4):
            raw = data.get(f"hint_{i}", "")
            if raw:
                # Format parameters safely
                formatted = raw.format(**{k: str(v) for k, v in rule_params.items()})
                hints.append(formatted)
                
        return hints
        
    def calculate_hint_penalty(self, hints_used: int) -> int:
        return hints_used * self.hint_cost_policy
