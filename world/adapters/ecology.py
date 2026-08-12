"""Ecology adapter — NetworkX food-web interactions."""
from __future__ import annotations
from typing import Dict, Tuple
import networkx as nx

class EcologyAdapter:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.biomass: Dict[str, float] = {}
        self.interactions: Dict[Tuple[str, str], float] = {}

    def add_species(self, name: str, biomass: float = 10.0) -> None:
        self.graph.add_node(name)
        self.biomass[name] = biomass

    def add_interaction(self, a: str, b: str, strength: float) -> None:
        self.graph.add_edge(a, b, weight=strength)
        self.interactions[(a, b)] = strength

    def step(self, dt: float = 0.1) -> Dict[str, float]:
        names = list(self.biomass.keys())
        delta = {n: 0.0 for n in names}
        for (a, b), w in self.interactions.items():
            na, nb = self.biomass.get(a, 0), self.biomass.get(b, 0)
            delta[a] += w * na * nb * 0.01
            delta[b] -= w * na * nb * 0.01
        for n in names:
            self.biomass[n] = max(0.1, round(self.biomass[n] + delta[n] * dt - 0.001 * self.biomass[n], 6))
        return dict(self.biomass)
