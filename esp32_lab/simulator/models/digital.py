
from dataclasses import dataclass

@dataclass
class DigitalState:
    value: int
    status: str # 'HIGH', 'LOW', 'FLOATING', 'CONFLICT'
