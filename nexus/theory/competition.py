"""Theory Competition — maintain competing explanations, update from evidence."""

from __future__ import annotations

from typing import Dict, List, Optional

from nexus.types import CompetingTheory


class TheoryCompetition:
    def __init__(self):
        self.theories: List[CompetingTheory] = []

    def seed_competitors(self, statements: List[str], predictions: Optional[List[Dict]] = None) -> List[CompetingTheory]:
        predictions = predictions or [{} for _ in statements]
        n = max(1, len(statements))
        prior = 1.0 / n
        self.theories = []
        for i, stmt in enumerate(statements):
            self.theories.append(
                CompetingTheory(
                    statement=stmt,
                    prior=prior,
                    posterior=prior,
                    predictions=predictions[i] if i < len(predictions) else {},
                )
            )
        return self.theories

    def update_from_observation(self, likelihoods: Dict[str, float]) -> None:
        """likelihoods: theory_id -> P(data|theory) in [0,1]."""
        if not self.theories:
            return
        scores = []
        for t in self.theories:
            lik = float(likelihoods.get(t.theory_id, 0.5))
            scores.append(t.posterior * max(0.01, lik))
        total = sum(scores) or 1.0
        for t, s in zip(self.theories, scores):
            t.posterior = s / total

    def ranking(self) -> List[CompetingTheory]:
        return sorted(self.theories, key=lambda t: t.posterior, reverse=True)

    def best(self) -> Optional[CompetingTheory]:
        r = self.ranking()
        return r[0] if r else None
