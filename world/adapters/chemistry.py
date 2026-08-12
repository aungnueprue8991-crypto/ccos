"""Chemistry adapter — simplified reaction kinetics."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Reaction:
    name: str
    reactants: Dict[str, float]
    products: Dict[str, float]
    rate: float = 0.1

class ChemistryAdapter:
    def __init__(self):
        self.species: Dict[str, float] = {}
        self.reactions: List[Reaction] = []

    def add_species(self, name: str, amount: float = 0.0) -> None:
        self.species[name] = float(amount)

    def add_reaction(self, reaction: Reaction) -> None:
        self.reactions.append(reaction)
        for n in list(reaction.reactants) + list(reaction.products):
            self.species.setdefault(n, 0.0)

    def step(self, dt: float = 1.0) -> Dict[str, float]:
        delta = {k: 0.0 for k in self.species}
        for rxn in self.reactions:
            rate = rxn.rate
            for name, coeff in rxn.reactants.items():
                rate *= max(self.species.get(name, 0.0), 0.0) ** coeff
            for name, coeff in rxn.reactants.items():
                delta[name] -= rate * coeff * dt
            for name, coeff in rxn.products.items():
                delta[name] = delta.get(name, 0.0) + rate * coeff * dt
        for k, d in delta.items():
            self.species[k] = max(0.0, round(self.species.get(k, 0.0) + d, 8))
        return dict(self.species)
