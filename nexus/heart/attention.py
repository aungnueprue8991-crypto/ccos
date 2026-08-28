"""Cognitive Heart — attention / salience / what deserves thought right now.

Does not think. Allocates cognitive budget.
priority ≈ curiosity + uncertainty + novelty + goal + anomaly + transfer − cost
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from nexus.drives.arbitration import DriveManager
from nexus.types import CognitiveObjective, DriveName, QVector


@dataclass
class SalienceItem:
    item_id: str
    description: str
    score: float
    factors: Dict[str, float] = field(default_factory=dict)
    domain: str = "general"


class CognitiveHeart:
    def __init__(self):
        self.drives = DriveManager()
        self.focus_history: List[SalienceItem] = []

    def evaluate_focus(
        self,
        observations: Optional[List[Dict[str, Any]]] = None,
        prediction_errors: Optional[List[Dict[str, Any]]] = None,
        contradictions: Optional[List[str]] = None,
        knowledge_gaps: Optional[List[str]] = None,
        archive_size: int = 0,
        competence: float = 0.5,
        resource_pressure: float = 0.2,
        q: Optional[QVector] = None,
        domain: str = "general",
    ) -> tuple[CognitiveObjective, List[SalienceItem]]:
        q = q or QVector()
        objective = self.drives.evaluate(
            observations=observations,
            prediction_errors=prediction_errors,
            contradictions=contradictions,
            archive_size=archive_size,
            competence=competence,
            resource_pressure=resource_pressure,
            q=q,
        )

        items: List[SalienceItem] = []
        prediction_errors = prediction_errors or []
        for i, err in enumerate(prediction_errors[:5]):
            surprise = float(err.get("surprise", 0.5))
            score = (
                0.35 * surprise
                + 0.25 * q.uncertainty
                + 0.2 * objective.priority
                + 0.15 * (1.0 - competence)
                - 0.1 * resource_pressure
            )
            items.append(
                SalienceItem(
                    item_id=f"err-{i}",
                    description=str(err.get("entity", "anomaly")),
                    score=max(0.0, min(1.0, score)),
                    factors={
                        "surprise": surprise,
                        "uncertainty": q.uncertainty,
                        "drive": objective.priority,
                    },
                    domain=domain,
                )
            )

        for i, gap in enumerate((knowledge_gaps or [])[:3]):
            items.append(
                SalienceItem(
                    item_id=f"gap-{i}",
                    description=gap,
                    score=0.4 + 0.1 * q.uncertainty,
                    factors={"gap": 1.0},
                    domain=domain,
                )
            )

        if not items:
            items.append(
                SalienceItem(
                    item_id="baseline",
                    description=f"explore {domain}",
                    score=0.35,
                    factors={"baseline": 1.0},
                    domain=domain,
                )
            )

        items.sort(key=lambda x: x.score, reverse=True)
        self.focus_history.extend(items[:3])
        self.focus_history = self.focus_history[-50:]

        objective.domain = domain
        return objective, items
