"""SCOS Benchmark Harness + multi-dimensional fitness evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class FitnessVector:
    accuracy: float = 0.0
    efficiency: float = 0.0
    robustness: float = 0.0
    generalization: float = 0.0
    reproducibility: float = 0.0
    safety: float = 0.0
    interpretability: float = 0.0
    resource_cost: float = 0.0
    novelty: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "accuracy": self.accuracy, "efficiency": self.efficiency,
            "robustness": self.robustness, "generalization": self.generalization,
            "reproducibility": self.reproducibility, "safety": self.safety,
            "interpretability": self.interpretability, "resource_cost": self.resource_cost,
            "novelty": self.novelty,
        }

    def scalar(self, weights: Optional[Dict[str, float]] = None) -> float:
        w = weights or {
            "accuracy": 1.0, "efficiency": 0.8, "robustness": 0.9,
            "generalization": 0.7, "reproducibility": 0.8, "safety": 1.2,
            "interpretability": 0.5, "resource_cost": 0.6, "novelty": 0.4,
        }
        d = self.to_dict()
        score = 0.0
        for k, weight in w.items():
            v = d.get(k, 0.0)
            if k == "resource_cost":
                v = max(0.0, 1.0 - v)
            score += weight * v
        return score


@dataclass
class BenchmarkResult:
    name: str
    fitness: FitnessVector
    raw_metrics: Dict[str, float] = field(default_factory=dict)
    passed: bool = False


class BenchmarkHarness:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._suites: Dict[str, Callable[[], Dict[str, float]]] = {}

    def register(self, name: str, fn: Callable[[], Dict[str, float]]) -> None:
        self._suites[name] = fn

    def run(self, name: str, thresholds: Optional[Dict[str, float]] = None) -> BenchmarkResult:
        if name not in self._suites:
            raise KeyError(f"Unknown benchmark suite: {name}")
        raw = self._suites[name]()
        fitness = FitnessVector(
            accuracy=raw.get("accuracy", 0.0), efficiency=raw.get("efficiency", 0.0),
            robustness=raw.get("robustness", 0.0), generalization=raw.get("generalization", 0.0),
            reproducibility=raw.get("reproducibility", 1.0), safety=raw.get("safety", 1.0),
            interpretability=raw.get("interpretability", 0.5), resource_cost=raw.get("resource_cost", 0.1),
            novelty=raw.get("novelty", 0.0),
        )
        thresholds = thresholds or {"accuracy": 0.7, "safety": 0.9}
        passed = all(raw.get(k, 0.0) >= v for k, v in thresholds.items())
        result = BenchmarkResult(name=name, fitness=fitness, raw_metrics=raw, passed=passed)
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="scos.benchmark.completed", producer_id="scos.benchmarks",
                payload={"name": name, "passed": passed, "fitness": fitness.to_dict(), "scalar": fitness.scalar()},
            ))
        return result
