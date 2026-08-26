"""Curiosity Allocation — expected_learning × usefulness × uncertainty / cost."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CuriosityScore:
    topic: str
    expected_learning: float
    usefulness: float
    uncertainty: float
    cost: float
    value: float  # (el * use * unc) / cost


class CuriosityAllocator:
    """
    value = (expected_learning * usefulness * uncertainty) / max(cost, eps)
    Prefer high information per unit cost (aligned with EIG/cost design).
    """

    def score(
        self,
        topic: str,
        expected_learning: float,
        usefulness: float,
        uncertainty: float,
        cost: float = 1.0,
    ) -> CuriosityScore:
        cost = max(1e-6, cost)
        value = (expected_learning * usefulness * uncertainty) / cost
        return CuriosityScore(
            topic=topic,
            expected_learning=expected_learning,
            usefulness=usefulness,
            uncertainty=uncertainty,
            cost=cost,
            value=round(value, 6),
        )

    def rank(self, candidates: List[CuriosityScore]) -> List[CuriosityScore]:
        return sorted(candidates, key=lambda c: c.value, reverse=True)
