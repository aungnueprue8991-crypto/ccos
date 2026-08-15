"""Biology adapter — logistic growth, mortality, and simple age structure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


def _q(x: float, nd: int = 6) -> float:
    return round(float(x), nd)


@dataclass
class Population:
    name: str
    count: float
    growth_rate: float = 0.05
    carrying_capacity: float = 1000.0
    mortality: float = 0.01
    age_mean: float = 1.0


@dataclass
class Cohort:
    age: float
    count: float


class BiologyAdapter:
    def __init__(self):
        self.populations: Dict[str, Population] = {}
        self.cohorts: Dict[str, List[Cohort]] = {}

    def add(self, pop: Population) -> None:
        self.populations[pop.name] = pop
        if pop.name not in self.cohorts:
            self.cohorts[pop.name] = [Cohort(age=pop.age_mean, count=pop.count)]

    def step(self, dt: float = 1.0) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for name, p in self.populations.items():
            n = p.count
            growth = p.growth_rate * n * (1.0 - n / max(p.carrying_capacity, 1e-9))
            death = p.mortality * n
            p.count = max(0.0, _q(n + (growth - death) * dt))
            p.age_mean = _q(p.age_mean + dt * 0.1)
            out[name] = p.count
            if name in self.cohorts and self.cohorts[name]:
                total = sum(c.count for c in self.cohorts[name]) or 1.0
                scale = p.count / total
                for c in self.cohorts[name]:
                    c.count = max(0.0, _q(c.count * scale))
                    c.age = _q(c.age + dt)
        return out

    def split_cohort(self, name: str, ages: List[float], fractions: List[float]) -> None:
        p = self.populations[name]
        fr = fractions or [1.0]
        s = sum(fr) or 1.0
        self.cohorts[name] = [
            Cohort(age=_q(a), count=_q(p.count * (f / s)))
            for a, f in zip(ages, fr)
        ]

    def harvest(self, name: str, amount: float) -> float:
        p = self.populations[name]
        taken = min(p.count, max(0.0, amount))
        p.count = _q(p.count - taken)
        return taken

    def carrying_pressure(self, name: str) -> float:
        p = self.populations[name]
        return _q(p.count / max(p.carrying_capacity, 1e-9))

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        return {
            n: {
                "count": p.count,
                "growth_rate": p.growth_rate,
                "K": p.carrying_capacity,
                "mortality": p.mortality,
                "age_mean": p.age_mean,
                "pressure": self.carrying_pressure(n),
            }
            for n, p in sorted(self.populations.items())
        }
