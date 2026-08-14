
from __future__ import annotations
import copy, random, threading
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from ags.shared.types import new_id, now_ts

@dataclass
class FitnessVector:
    learning: float = 0.0
    discovery: float = 0.0
    cooperation: float = 0.0
    prediction: float = 0.0
    scientific_reliability: float = 0.0
    resource_efficiency: float = 0.0
    adaptability: float = 0.0
    constitutional_compliance: float = 1.0
    def as_dict(self):
        return asdict(self)
    def dominated_by(self, other: "FitnessVector") -> bool:
        a, b = self.as_dict(), other.as_dict()
        return all(b[k] >= a[k] for k in a) and any(b[k] > a[k] for k in a)

@dataclass
class StructuredGenome:
    genome_id: str
    lineage: List[str] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)
    generation: int = 0
    traits: Dict[str, float] = field(default_factory=lambda: {"curiosity": 0.7, "persistence": 0.6, "caution": 0.4, "exploration": 0.5, "cooperation": 0.5})
    learning: Dict[str, float] = field(default_factory=lambda: {"learning_rate": 0.25, "plasticity": 0.5, "consolidation": 0.8, "exploration_rate": 0.3})
    cognition: Dict[str, float] = field(default_factory=lambda: {"hypothesis_generation": 0.5, "abstraction": 0.5, "planning": 0.5, "falsification": 0.5})
    skill_priors: Dict[str, float] = field(default_factory=dict)
    mutation_log: List[str] = field(default_factory=list)
    def clamp_all(self):
        for d in (self.traits, self.learning, self.cognition):
            for k in d: d[k] = max(0.05, min(0.99, float(d[k])))

def mutate_genome(g, rate=0.1, scale=0.05, rng=None):
    rng = rng or random.Random()
    child = copy.deepcopy(g)
    child.genome_id = new_id(); child.parents = [g.genome_id]
    child.lineage = list(g.lineage)+[child.genome_id]; child.generation = g.generation+1
    child.mutation_log = []
    for group_name, group in [("traits", child.traits), ("learning", child.learning), ("cognition", child.cognition)]:
        for k in group:
            if rng.random() < rate:
                old = group[k]; group[k] = old + rng.uniform(-scale, scale)
                child.mutation_log.append(f"{group_name}.{k}:{old:.3f}->{group[k]:.3f}")
    child.clamp_all(); return child

def crossover(a, b, rng=None):
    rng = rng or random.Random()
    child = copy.deepcopy(a)
    child.genome_id = new_id(); child.parents = [a.genome_id, b.genome_id]
    child.lineage = list(dict.fromkeys(a.lineage + b.lineage + [child.genome_id]))
    child.generation = max(a.generation, b.generation)+1
    for group_name in ("traits", "learning", "cognition"):
        ga, gb, gc = getattr(a, group_name), getattr(b, group_name), getattr(child, group_name)
        for k in gc:
            gc[k] = (ga.get(k, 0.5)+gb.get(k, 0.5))/2
    child.skill_priors = {k: (a.skill_priors.get(k,0.3)+b.skill_priors.get(k,0.3))/2 for k in set(a.skill_priors)|set(b.skill_priors)}
    child.mutation_log = [f"crossover"]; child.clamp_all(); return child

@dataclass
class BirthTransaction:
    transaction_id: str; parent_ids: List[str]; child_genome_id: str
    approved: bool; reason: str; fitness: Optional[FitnessVector]=None
    timestamp: float = field(default_factory=now_ts)

class ControlledReproduction:
    def __init__(self, max_population=10, max_offspring_per_parent=2, min_fitness_discovery=0.1):
        self.max_population = max_population; self.max_offspring = max_offspring_per_parent
        self.min_fitness_discovery = min_fitness_discovery
        self.population: Dict[str, StructuredGenome] = {}; self.fitness: Dict[str, FitnessVector] = {}
        self.offspring_count: Dict[str, int] = {}; self.lineage_ledger: List[BirthTransaction] = []
        self._lock = threading.Lock(); self.reproduction_enabled = True
    def register(self, agent_id, genome, fit=None):
        with self._lock:
            self.population[agent_id]=genome; self.fitness[agent_id]=fit or FitnessVector()
            self.offspring_count.setdefault(agent_id, 0)
    def request_birth(self, parent_ids, mode="mutate", rng=None):
        rng = rng or random.Random(42); tid = new_id()
        with self._lock:
            if not self.reproduction_enabled:
                tx=BirthTransaction(tid,parent_ids,"",False,"reproduction_disabled"); self.lineage_ledger.append(tx); return tx
            if len(self.population)>=self.max_population:
                tx=BirthTransaction(tid,parent_ids,"",False,"population_limit"); self.lineage_ledger.append(tx); return tx
            for pid in parent_ids:
                if pid not in self.population:
                    tx=BirthTransaction(tid,parent_ids,"",False,"unknown_parent"); self.lineage_ledger.append(tx); return tx
                if self.offspring_count.get(pid,0)>=self.max_offspring:
                    tx=BirthTransaction(tid,parent_ids,"",False,"offspring_quota"); self.lineage_ledger.append(tx); return tx
                fit=self.fitness.get(pid, FitnessVector())
                if fit.discovery < self.min_fitness_discovery and fit.learning < 0.2:
                    tx=BirthTransaction(tid,parent_ids,"",False,"insufficient_fitness"); self.lineage_ledger.append(tx); return tx
            if mode=="crossover" and len(parent_ids)>=2:
                child_g=crossover(self.population[parent_ids[0]], self.population[parent_ids[1]], rng)
            else:
                child_g=mutate_genome(self.population[parent_ids[0]], rng=rng)
            child_id=f"child-{child_g.genome_id[:8]}"
            self.population[child_id]=child_g; self.fitness[child_id]=FitnessVector()
            for pid in parent_ids: self.offspring_count[pid]=self.offspring_count.get(pid,0)+1
            tx=BirthTransaction(tid,parent_ids,child_g.genome_id,True,"birth_authorized",self.fitness[child_id])
            self.lineage_ledger.append(tx); return tx
    def summary(self):
        return {"population":len(self.population),"births_approved":sum(1 for t in self.lineage_ledger if t.approved),
                "births_denied":sum(1 for t in self.lineage_ledger if not t.approved),"ledger_size":len(self.lineage_ledger)}
