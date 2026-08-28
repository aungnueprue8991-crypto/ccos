"""Capability Router — task → best model / engine / tool (learnable priors)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from nexus.routing_models.profiler import ModelCapabilityProfiler, ModelProfile


@dataclass
class RouteDecision:
    task_type: str
    chosen: str
    score: float
    alternatives: List[str] = field(default_factory=list)
    reason: str = ""


class CapabilityRouter:
    def __init__(self, profiler: Optional[ModelCapabilityProfiler] = None):
        self.profiler = profiler or ModelCapabilityProfiler()
        self.outcome_boost: Dict[str, float] = {}

    def route(self, task_type: str, prefer_cheap: bool = False) -> RouteDecision:
        scored = []
        for p in self.profiler.all_profiles():
            s = p.score_for(task_type) + self.outcome_boost.get(p.model_id, 0.0)
            if prefer_cheap:
                s = 0.7 * s + 0.3 * (1.0 - p.cost)
            scored.append((s, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        best_s, best = scored[0]
        alts = [p.model_id for _, p in scored[1:3]]
        return RouteDecision(
            task_type=task_type,
            chosen=best.model_id,
            score=round(best_s, 4),
            alternatives=alts,
            reason=f"best score_for({task_type})",
        )

    def observe(self, model_id: str, success: bool) -> None:
        delta = 0.05 if success else -0.04
        self.outcome_boost[model_id] = max(-0.3, min(0.3, self.outcome_boost.get(model_id, 0.0) + delta))
