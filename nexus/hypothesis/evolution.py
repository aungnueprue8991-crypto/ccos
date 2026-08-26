"""Hypothesis Evolution — refine hypotheses after partial failure / boundary discovery."""

from __future__ import annotations

from typing import List, Optional

from nexus.types import Hypothesis


class HypothesisEvolution:
    def __init__(self):
        self.lineage: List[Hypothesis] = []

    def evolve(
        self,
        hyp: Hypothesis,
        outcome: str,
        boundary_hint: Optional[str] = None,
    ) -> Hypothesis:
        """outcome: supported|mixed|falsified."""
        if outcome == "supported":
            child = Hypothesis(
                statement=hyp.statement,
                predictions=dict(hyp.predictions),
                confidence=min(0.95, hyp.confidence + 0.1),
                falsifiers=list(hyp.falsifiers),
                idea_id=hyp.idea_id,
                question_id=hyp.question_id,
                status="supported",
            )
        elif outcome == "mixed":
            boundary = boundary_hint or "under restricted conditions"
            child = Hypothesis(
                statement=f"{hyp.statement} — only {boundary}",
                predictions=dict(hyp.predictions),
                confidence=max(0.3, hyp.confidence - 0.05),
                falsifiers=list(hyp.falsifiers) + [f"fails outside {boundary}"],
                idea_id=hyp.idea_id,
                question_id=hyp.question_id,
                status="proposed",
            )
        else:  # falsified
            child = Hypothesis(
                statement=f"Revised after falsification of: {hyp.statement[:60]}",
                predictions={},
                confidence=0.3,
                falsifiers=["previous form falsified"],
                idea_id=hyp.idea_id,
                question_id=hyp.question_id,
                status="proposed",
            )
        self.lineage.append(hyp)
        self.lineage.append(child)
        return child
