"""Efficiency Engine — permanent drive to improve capability/resource ratio."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EfficiencyReport:
    tokens_proxy: float = 0.0
    steps: int = 0
    successes: int = 0
    failures: int = 0
    cost_score: float = 0.0
    capability_score: float = 0.0
    ratio: float = 0.0
    recommendations: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "tokens_proxy": self.tokens_proxy,
            "steps": self.steps,
            "successes": self.successes,
            "failures": self.failures,
            "cost_score": self.cost_score,
            "capability_score": self.capability_score,
            "ratio": self.ratio,
            "recommendations": list(self.recommendations),
        }


class EfficiencyEngine:
    def __init__(self):
        self.history: List[Dict[str, float]] = []

    def record(self, tokens_proxy: float, steps: int, success: bool) -> None:
        self.history.append(
            {
                "tokens": tokens_proxy,
                "steps": float(steps),
                "success": 1.0 if success else 0.0,
            }
        )
        if len(self.history) > 200:
            self.history = self.history[-200:]

    def report(self) -> EfficiencyReport:
        if not self.history:
            return EfficiencyReport(recommendations=["insufficient_data"])
        tokens = sum(h["tokens"] for h in self.history)
        steps = int(sum(h["steps"] for h in self.history))
        successes = int(sum(h["success"] for h in self.history))
        failures = len(self.history) - successes
        cost = tokens / max(1, len(self.history)) + 0.1 * (steps / max(1, len(self.history)))
        cap = successes / max(1, len(self.history))
        ratio = cap / (cost + 1e-6)
        recs = []
        if cost > 2.0 and cap < 0.5:
            recs.append("reduce_reasoning_depth")
        if tokens / max(1, len(self.history)) > 5:
            recs.append("prefer_cheaper_model_route")
        if steps / max(1, len(self.history)) > 20:
            recs.append("shorten_event_loop")
        if not recs:
            recs.append("maintain_current_policy")
        return EfficiencyReport(
            tokens_proxy=round(tokens, 2),
            steps=steps,
            successes=successes,
            failures=failures,
            cost_score=round(cost, 4),
            capability_score=round(cap, 4),
            ratio=round(ratio, 4),
            recommendations=recs,
        )
