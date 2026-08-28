"""Ecology adapter — multi-species biomass with interaction matrix."""

from __future__ import annotations

from typing import Dict, List, Tuple


def _q(x: float, nd: int = 6) -> float:
    return round(float(x), nd)


class EcologyAdapter:
    def __init__(self):
        self.biomass: Dict[str, float] = {}
        self.interactions: Dict[Tuple[str, str], float] = {}

    def add_species(self, name: str, biomass: float = 10.0) -> None:
        self.biomass[name] = float(biomass)

    def add_interaction(self, predator: str, prey: str, strength: float = 0.1) -> None:
        self.interactions[(predator, prey)] = float(strength)

    def step(self, dt: float = 1.0) -> Dict[str, float]:
        delta = {k: 0.0 for k in self.biomass}
        for (pred, prey), strength in self.interactions.items():
            if pred not in self.biomass or prey not in self.biomass:
                continue
            flow = strength * self.biomass[pred] * self.biomass[prey] * 0.01 * dt
            delta[prey] -= flow
            delta[pred] += flow * 0.3
        for k in list(self.biomass):
            self.biomass[k] = max(0.0, _q(self.biomass[k] + delta.get(k, 0.0)))
        return dict(self.biomass)

    def top_species(self, n: int = 3) -> List[Tuple[str, float]]:
        return sorted(self.biomass.items(), key=lambda kv: -kv[1])[:n]

    def snapshot(self) -> Dict[str, float]:
        return {k: _q(v) for k, v in sorted(self.biomass.items())}
