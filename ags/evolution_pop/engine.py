"""Phase 7 — population-level evolution statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ags.genome.traits import AgentGenome
from ags.genome.manager import GenomeManager


@dataclass
class GenerationStats:
    generation: int
    population: int
    mean_knowledge: float
    mean_discoveries: float
    fitness: float


class PopulationEvolution:
    def __init__(self) -> None:
        self.history: List[GenerationStats] = []

    def record_generation(self, generation: int, agents_meta: List[Dict[str, Any]]) -> GenerationStats:
        n = max(1, len(agents_meta))
        mk = sum(a.get("knowledge", 0) for a in agents_meta) / n
        md = sum(a.get("discoveries", 0) for a in agents_meta) / n
        fitness = mk * 0.6 + md * 0.4
        stats = GenerationStats(generation, len(agents_meta), mk, md, fitness)
        self.history.append(stats)
        return stats

    def improving(self) -> bool:
        if len(self.history) < 2:
            return False
        return self.history[-1].fitness >= self.history[-2].fitness
