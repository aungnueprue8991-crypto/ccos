"""Experiment Selection — maximize expected information gain / cost.

Proxy EIG for discrete theory discrimination:
  EIG ≈ H(prior) - E[H(posterior|outcome)]
We use entropy of theory posteriors as prior uncertainty.
Score = EIG_proxy / cost.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional


def _entropy(probs: List[float]) -> float:
    h = 0.0
    for p in probs:
        if p > 1e-12:
            h -= p * math.log(p, 2)
    return h


@dataclass
class ExperimentCandidate:
    name: str
    expected_ig: float
    cost: float
    risk: float
    score: float
    discriminates: List[str]


class ExperimentSelector:
    def score_experiment(
        self,
        name: str,
        theory_posteriors: Dict[str, float],
        cost: float = 1.0,
        risk: float = 0.1,
        relevance: float = 1.0,
    ) -> ExperimentCandidate:
        probs = list(theory_posteriors.values())
        s = sum(probs) or 1.0
        probs = [p / s for p in probs]
        eig = _entropy(probs)
        eig_proxy = eig * 0.5 * relevance
        cost = max(1e-6, cost)
        score = eig_proxy / (cost * (1.0 + risk))
        return ExperimentCandidate(
            name=name,
            expected_ig=round(eig_proxy, 4),
            cost=cost,
            risk=risk,
            score=round(score, 4),
            discriminates=list(theory_posteriors.keys()),
        )

    def choose(
        self,
        candidates: List[ExperimentCandidate],
    ) -> Optional[ExperimentCandidate]:
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.score)
