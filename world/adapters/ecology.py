"""Ecology adapter — food-web biomass dynamics (Lotka–Volterra style on a digraph)."""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import networkx as nx


def _q(x: float, nd: int = 6) -> float:
    return round(float(x), nd)


class EcologyAdapter:
    def __init__(self, basal_growth: float = 0.05, decay: float = 0.01):
        self.graph = nx.DiGraph()
        self.biomass: Dict[str, float] = {}
        self.interactions: Dict[Tuple[str, str], float] = {}
        self.basal_growth = basal_growth
        self.decay = decay
        self.trophic: Dict[str, str] = {}

    def add_species(self, name: str, biomass: float = 10.0, role: str = "consumer") -> None:
        self.graph.add_node(name, role=role)
        self.biomass[name] = float(biomass)
        self.trophic[name] = role

    def add_interaction(self, predator: str, prey: str, strength: float) -> None:
        self.graph.add_edge(predator, prey, weight=strength)
        self.interactions[(predator, prey)] = float(strength)

    def step(self, dt: float = 0.1) -> Dict[str, float]:
        names = list(self.biomass.keys())
        delta = {n: 0.0 for n in names}
        for n in names:
            if self.trophic.get(n) == "producer":
                delta[n] += self.basal_growth * self.biomass[n]
            delta[n] -= self.decay * self.biomass[n]
        for (pred, prey), w in self.interactions.items():
            np_ = self.biomass.get(pred, 0.0)
            ny = self.biomass.get(prey, 0.0)
            flow = w * np_ * ny * 0.01
            delta[pred] = delta.get(pred, 0.0) + flow * 0.5
            delta[prey] = delta.get(prey, 0.0) - flow
        for n in names:
            self.biomass[n] = max(0.1, _q(self.biomass[n] + delta.get(n, 0.0) * dt))
        return dict(self.biomass)

    def diversity(self) -> float:
        total = sum(self.biomass.values()) or 1.0
        h = 0.0
        for b in self.biomass.values():
            p = b / total
            if p > 0:
                h -= p * math.log(p + 1e-15)
        return _q(h)

    def top_predators(self, n: int = 3) -> List[Tuple[str, float]]:
        return sorted(self.biomass.items(), key=lambda kv: -kv[1])[:n]

    def snapshot(self) -> Dict[str, float]:
        return {k: _q(v) for k, v in sorted(self.biomass.items())}
