"""Selection policies for experimental evolution."""
from __future__ import annotations
from typing import Dict, List
from ags.evolution.reproduction import FitnessVector
from ags.evolution.fitness import pareto_front

def select_parents(fitness: Dict[str, FitnessVector], k: int = 2) -> List[str]:
    front = pareto_front(fitness)
    if len(front) >= k:
        return front[:k]
    ranked = sorted(fitness.keys(), key=lambda i: fitness[i].discovery, reverse=True)
    out = list(front)
    for i in ranked:
        if i not in out:
            out.append(i)
        if len(out) >= k:
            break
    return out[:k]
