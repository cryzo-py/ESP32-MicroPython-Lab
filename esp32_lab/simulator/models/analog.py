
from dataclasses import dataclass
from typing import Optional

@dataclass
class AnalogState:
    value: Optional[int]
    status: str  # 'VALUE', 'FLOATING', 'CONFLICT', 'INVALID'
