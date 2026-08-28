"""Salience / efficiency layer — novelty, surprise, uncertainty, contradiction, relevance."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set

from nexus.perception.observation import StructuredObservation


@dataclass
class SalienceScore:
    novelty: float = 0.0
    surprise: float = 0.0
    uncertainty: float = 0.0
    contradiction: float = 0.0
    relevance: float = 0.0
    aggregate: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


class SalienceEngine:
    def __init__(self):
        self.seen_texts: Set[str] = set()

    def score(
        self,
        obs: StructuredObservation,
        state_uncertainty: float = 0.5,
        known_contradictions: int = 0,
        goal_keywords: Optional[List[str]] = None,
    ) -> SalienceScore:
        text = (obs.text or "").lower().strip()
        novelty = 0.8 if text and text not in self.seen_texts else 0.15
        if text:
            self.seen_texts.add(text[:300])

        surprise = 0.2
        if obs.predicted is not None and obs.actual is not None:
            err = abs(float(obs.actual) - float(obs.predicted))
            surprise = min(1.0, err)
            surprise = 0.5 * surprise + 0.5 * (1.0 - obs.prediction_confidence)

        uncertainty = min(1.0, 0.5 * state_uncertainty + 0.5 * (1.0 - obs.prediction_confidence))
        contradiction = min(1.0, 0.2 * known_contradictions)

        relevance = 0.4
        if goal_keywords:
            hits = sum(1 for k in goal_keywords if k.lower() in text)
            relevance = min(1.0, 0.3 + 0.2 * hits)
        relevance = max(relevance, obs.salience_hint)

        agg = (
            0.25 * novelty
            + 0.30 * surprise
            + 0.20 * uncertainty
            + 0.10 * contradiction
            + 0.15 * relevance
        )
        return SalienceScore(
            novelty=round(novelty, 4),
            surprise=round(surprise, 4),
            uncertainty=round(uncertainty, 4),
            contradiction=round(contradiction, 4),
            relevance=round(relevance, 4),
            aggregate=round(min(1.0, agg), 4),
        )
