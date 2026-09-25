from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal

@dataclass
class EvaluationRule:
    id: str
    type: Literal["code_pin", "code_import", "topology", "component", "behavior"]
    required: bool = True
    weight: int = 10
    
    # Specific fields for code_pin
    gpio: Optional[int] = None
    mode: Optional[str] = None  # e.g., "OUT", "IN", "PWM", "ADC"
    
    # Specific fields for code_import
    module_name: Optional[str] = None
    class_name: Optional[str] = None
    
    # Specific fields for topology
    component_type: Optional[str] = None
    pin_name: Optional[str] = None
    
    # Specific fields for component
    count: Optional[int] = None

@dataclass
class EvaluationItem:
    id: str
    category: Literal["CODE", "PHYSICAL", "BEHAVIOR", "LEGACY"]
    status: Literal["PASS", "FAIL", "WARNING", "NOT_APPLICABLE"]
    score: int
    max_score: int
    message: str
    technical_message: str
    pedagogical_message: str
    details: Dict[str, Any] = field(default_factory=dict)
