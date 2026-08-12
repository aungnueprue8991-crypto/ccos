"""Biology adapter — logistic population growth."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

@dataclass
class Population:
    name: str
    count: float
    growth_rate: float = 0.05
    carrying_capacity: float = 1000.0

class BiologyAdapter:
    def __init__(self):
        self.populations: Dict[str, Population] = {}

    def add(self, pop: Population) -> None:
        self.populations[pop.name] = pop

    def step(self, dt: float = 1.0) -> Dict[str, float]:
        out = {}
        for name, p in self.populations.items():
            n = p.count
            dn = p.growth_rate * n * (1.0 - n / max(p.carrying_capacity, 1e-9)) * dt
            p.count = max(0.0, round(n + dn, 6))
            out[name] = p.count
        return out
