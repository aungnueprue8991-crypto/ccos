"""Meta-cognition policy learning — route weights updated from outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


DEFAULT_WEIGHTS: Dict[str, float] = {
    "thought_engine": 0.5,
    "question_engine": 0.5,
    "analogy_engine": 0.4,
    "serendipity_engine": 0.3,
    "reasoning_engine": 0.6,
    "simulation_engine": 0.4,
    "experiment_manager": 0.5,
    "theory_competition": 0.5,
    "dream_engine": 0.25,
}


@dataclass
class RoutingPolicy:
    weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    learning_rate: float = 0.08
    history: List[Dict] = field(default_factory=list)

    def prior(self, engine: str, state: Optional[Dict[str, float]] = None) -> float:
        w = self.weights.get(engine, 0.4)
        state = state or {}
        if state.get("uncertainty", 0) > 0.6 and engine == "simulation_engine":
            w += 0.15
        if state.get("novelty_pressure", 0) > 0.5 and engine in (
            "serendipity_engine",
            "dream_engine",
            "analogy_engine",
        ):
            w += 0.12
        if state.get("contradiction", 0) > 0.4 and engine == "theory_competition":
            w += 0.15
        if state.get("surprise", 0) > 0.7 and engine == "question_engine":
            w += 0.1
        return max(0.05, min(1.0, w))

    def rank_engines(self, engines: List[str], state: Optional[Dict[str, float]] = None) -> List[str]:
        return sorted(engines, key=lambda e: self.prior(e, state), reverse=True)

    def update(
        self,
        used_engines: List[str],
        success: bool,
        transfer: bool = False,
        state: Optional[Dict[str, float]] = None,
    ) -> None:
        delta = self.learning_rate if success else -0.5 * self.learning_rate
        if transfer:
            delta += 0.5 * self.learning_rate
        for e in used_engines:
            self.weights[e] = max(0.05, min(1.0, self.weights.get(e, 0.4) + delta))
        for e, v in list(self.weights.items()):
            if e not in used_engines:
                self.weights[e] = 0.95 * v + 0.05 * DEFAULT_WEIGHTS.get(e, 0.4)
        self.history.append(
            {
                "used": list(used_engines),
                "success": success,
                "transfer": transfer,
                "weights": dict(self.weights),
            }
        )

    def suggest_pipeline(self, state: Optional[Dict[str, float]] = None) -> List[str]:
        candidates = [
            "thought_engine",
            "question_engine",
            "reasoning_engine",
            "theory_competition",
            "simulation_engine",
            "experiment_manager",
        ]
        ranked = self.rank_engines(candidates, state)
        return ranked[:4]
