"""Input Efficiency Engine — salience bottleneck before expensive cognition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from nexus.perception.observation import StructuredObservation
from nexus.perception.salience import SalienceEngine, SalienceScore


@dataclass
class FilteredBatch:
    kept: List[StructuredObservation]
    dropped: int
    scores: List[SalienceScore]
    threshold: float


class InputEfficiencyEngine:
    def __init__(self, threshold: float = 0.35, max_keep: int = 15):
        self.threshold = threshold
        self.max_keep = max_keep
        self.salience = SalienceEngine()

    def filter(
        self,
        observations: List[StructuredObservation],
        state_uncertainty: float = 0.5,
        goal_keywords: Optional[List[str]] = None,
    ) -> FilteredBatch:
        scored = []
        for obs in observations:
            s = self.salience.score(obs, state_uncertainty=state_uncertainty, goal_keywords=goal_keywords)
            scored.append((s.aggregate, obs, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        kept = []
        scores = []
        for agg, obs, s in scored:
            if agg >= self.threshold and len(kept) < self.max_keep:
                kept.append(obs)
                scores.append(s)
        return FilteredBatch(
            kept=kept,
            dropped=max(0, len(observations) - len(kept)),
            scores=scores,
            threshold=self.threshold,
        )
