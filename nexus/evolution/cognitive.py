"""Cognitive Evolution — select / mutate / recombine strategy genomes.

Strategies are pipelines + traits; fitness from experiment/transfer outcomes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ags.shared.types import new_id
from nexus.evolution.map_elites import CognitiveMapElites, StrategyCell


PIPELINE_GENES = (
    "thought",
    "analogy",
    "serendipity",
    "reason",
    "causal",
    "mad",
    "simulation",
    "experiment",
    "abstraction",
    "transfer",
    "dream",
)


@dataclass
class StrategyGenome:
    genome_id: str = field(default_factory=new_id)
    name: str = ""
    pipeline: List[str] = field(default_factory=list)
    traits: Dict[str, float] = field(default_factory=dict)
    fitness: float = 0.4
    lineage: List[str] = field(default_factory=list)

    def copy(self) -> "StrategyGenome":
        return StrategyGenome(
            name=self.name,
            pipeline=list(self.pipeline),
            traits=dict(self.traits),
            fitness=self.fitness,
            lineage=list(self.lineage) + [self.genome_id],
        )


class CognitiveEvolution:
    def __init__(self, seed: int = 7, population_size: int = 12):
        self.rng = random.Random(seed)
        self.population: List[StrategyGenome] = []
        self.map_elites = CognitiveMapElites()
        self.history: List[Dict] = []
        self._seed_population(population_size)

    def _seed_population(self, n: int) -> None:
        templates = [
            ("reason_exp", ["thought", "reason", "experiment"], {"analytical": 0.8, "causal": 0.7}),
            ("analogy_transfer", ["analogy", "transfer", "reason"], {"analytical": 0.7, "causal": 0.2}),
            ("serendipity_dream", ["serendipity", "dream", "thought"], {"analytical": 0.2, "causal": 0.3}),
            ("causal_sim", ["causal", "simulation", "experiment"], {"analytical": 0.6, "causal": 0.9}),
            ("full_science", ["thought", "reason", "mad", "experiment", "abstraction"], {"analytical": 0.5, "causal": 0.5}),
        ]
        for name, pipe, traits in templates:
            self.population.append(StrategyGenome(name=name, pipeline=pipe, traits=traits, fitness=0.45))
        while len(self.population) < n:
            self.population.append(self.mutate(self.rng.choice(self.population)))

    def mutate(self, parent: StrategyGenome, rate: float = 0.35) -> StrategyGenome:
        child = parent.copy()
        child.name = f"mut_{parent.name[:12]}"
        pipe = list(child.pipeline)
        if self.rng.random() < rate and pipe:
            i = self.rng.randrange(len(pipe))
            pipe[i] = self.rng.choice(PIPELINE_GENES)
        if self.rng.random() < rate:
            pipe.append(self.rng.choice(PIPELINE_GENES))
        if self.rng.random() < rate and len(pipe) > 2:
            pipe.pop(self.rng.randrange(len(pipe)))
        child.pipeline = pipe[:8]
        for k in list(child.traits):
            if self.rng.random() < rate:
                child.traits[k] = max(0.0, min(1.0, child.traits[k] + self.rng.uniform(-0.15, 0.15)))
        child.fitness = parent.fitness * 0.9
        return child

    def recombine(self, a: StrategyGenome, b: StrategyGenome) -> StrategyGenome:
        cut = max(1, min(len(a.pipeline), len(b.pipeline)) // 2)
        pipe = a.pipeline[:cut] + b.pipeline[cut:]
        traits = {}
        for k in set(a.traits) | set(b.traits):
            traits[k] = 0.5 * a.traits.get(k, 0.5) + 0.5 * b.traits.get(k, 0.5)
        child = StrategyGenome(
            name=f"x_{a.name[:6]}_{b.name[:6]}",
            pipeline=pipe[:8],
            traits=traits,
            fitness=0.5 * (a.fitness + b.fitness),
            lineage=[a.genome_id, b.genome_id],
        )
        return child

    def select(self, k: int = 3) -> List[StrategyGenome]:
        ranked = sorted(self.population, key=lambda g: g.fitness, reverse=True)
        return ranked[:k]

    def tournament(self) -> StrategyGenome:
        contenders = self.rng.sample(self.population, k=min(3, len(self.population)))
        return max(contenders, key=lambda g: g.fitness)

    def evolve_generation(self) -> List[StrategyGenome]:
        elites = self.select(k=3)
        next_pop = [e.copy() for e in elites]
        while len(next_pop) < len(self.population):
            if self.rng.random() < 0.5:
                next_pop.append(self.mutate(self.tournament()))
            else:
                next_pop.append(self.recombine(self.tournament(), self.tournament()))
        self.population = next_pop
        for g in elites:
            self.map_elites.try_add(
                g.name,
                g.traits.get("analytical", 0.5),
                g.traits.get("causal", 0.5),
                g.pipeline,
                g.fitness,
            )
        self.history.append({"elites": [e.name for e in elites], "best_fit": elites[0].fitness})
        return elites

    def observe(self, genome: StrategyGenome, success: bool, transfer: bool = False) -> None:
        delta = 0.06 if success else -0.04
        if transfer:
            delta += 0.05
        genome.fitness = max(0.05, min(1.0, genome.fitness + delta))
        self.map_elites.observe_outcome(
            StrategyCell(
                cell_id="x",
                analytical=genome.traits.get("analytical", 0.5),
                causal=genome.traits.get("causal", 0.5),
                name=genome.name,
                pipeline=genome.pipeline,
                fitness=genome.fitness,
            ),
            success=success,
            transfer=transfer,
        )
