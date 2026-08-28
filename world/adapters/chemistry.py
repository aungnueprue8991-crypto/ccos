"""Chemistry adapter — mass-action kinetics with optional Arrhenius temperature dependence."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List


def _q(x: float, nd: int = 8) -> float:
    return round(float(x), nd)


@dataclass
class Reaction:
    name: str
    reactants: Dict[str, float]
    products: Dict[str, float]
    rate: float = 0.1
    activation_energy: float = 0.0
    reversible: bool = False
    reverse_rate: float = 0.0


class ChemistryAdapter:
    def __init__(self, temperature_k: float = 298.15):
        self.species: Dict[str, float] = {}
        self.reactions: List[Reaction] = []
        self.temperature_k = temperature_k

    def add_species(self, name: str, amount: float = 0.0) -> None:
        self.species[name] = float(amount)

    def add_reaction(self, reaction: Reaction) -> None:
        self.reactions.append(reaction)
        for n in list(reaction.reactants) + list(reaction.products):
            self.species.setdefault(n, 0.0)

    def set_temperature(self, temp_k: float) -> None:
        self.temperature_k = max(1.0, float(temp_k))

    def _effective_rate(self, rxn: Reaction) -> float:
        k = rxn.rate
        if rxn.activation_energy > 0:
            k *= math.exp(-rxn.activation_energy / max(self.temperature_k, 1.0))
        return k

    def step(self, dt: float = 1.0) -> Dict[str, float]:
        delta = {k: 0.0 for k in self.species}
        for rxn in self.reactions:
            rate = self._effective_rate(rxn)
            for name, coeff in rxn.reactants.items():
                rate *= max(self.species.get(name, 0.0), 0.0) ** coeff
            for name, coeff in rxn.reactants.items():
                delta[name] = delta.get(name, 0.0) - rate * coeff * dt
            for name, coeff in rxn.products.items():
                delta[name] = delta.get(name, 0.0) + rate * coeff * dt
            if rxn.reversible and rxn.reverse_rate > 0:
                rev = rxn.reverse_rate
                for name, coeff in rxn.products.items():
                    rev *= max(self.species.get(name, 0.0), 0.0) ** coeff
                for name, coeff in rxn.products.items():
                    delta[name] = delta.get(name, 0.0) - rev * coeff * dt
                for name, coeff in rxn.reactants.items():
                    delta[name] = delta.get(name, 0.0) + rev * coeff * dt
        for k, d in delta.items():
            self.species[k] = max(0.0, _q(self.species.get(k, 0.0) + d))
        return dict(self.species)

    def total_mass(self) -> float:
        return _q(sum(self.species.values()))

    def snapshot(self) -> Dict[str, float]:
        return {k: _q(v) for k, v in sorted(self.species.items())}
