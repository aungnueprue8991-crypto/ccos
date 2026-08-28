"""Idle Cognition Scheduler — highest-value autonomous work under budget."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class IdleTask:
    name: str
    priority: float
    kind: str  # research|efficiency|memory|serendipity|health
    payload: Dict[str, Any] = field(default_factory=dict)


class IdleCognitionScheduler:
    """
    Priority order (blueprint):
    user > health > maintenance > research > self-improve > consolidation
    > efficiency > cross-domain > serendipity > long-horizon
    """

    BASE = {
        "health": 1.0,
        "maintenance": 0.9,
        "research": 0.75,
        "self_improve": 0.7,
        "consolidation": 0.6,
        "efficiency": 0.55,
        "cross_domain": 0.5,
        "serendipity": 0.35,
        "long_horizon": 0.3,
    }

    def __init__(self, budget: float = 1.0):
        self.budget = budget
        self.queue: List[IdleTask] = []

    def enqueue(self, name: str, kind: str, urgency: float = 0.5, payload: Optional[Dict] = None) -> None:
        base = self.BASE.get(kind, 0.4)
        self.queue.append(
            IdleTask(name=name, priority=base * (0.5 + 0.5 * urgency), kind=kind, payload=payload or {})
        )
        self.queue.sort(key=lambda t: t.priority, reverse=True)

    def from_signals(
        self,
        unresolved_questions: int = 0,
        contradictions: int = 0,
        efficiency_ratio: float = 0.5,
        capability_gaps: Optional[List[str]] = None,
    ) -> List[IdleTask]:
        self.queue.clear()
        if unresolved_questions > 0:
            self.enqueue("research_unresolved", "research", urgency=min(1.0, unresolved_questions / 10))
        if contradictions > 0:
            self.enqueue("investigate_contradictions", "research", urgency=min(1.0, contradictions / 5))
        if efficiency_ratio < 0.3:
            self.enqueue("efficiency_search", "efficiency", urgency=0.8)
        gaps = capability_gaps or []
        if gaps:
            self.enqueue("fill_capability_gap", "self_improve", urgency=0.7, payload={"gaps": gaps})
        self.enqueue("memory_consolidation", "consolidation", urgency=0.4)
        self.enqueue("cross_domain_scan", "cross_domain", urgency=0.45)
        self.enqueue("serendipity_sample", "serendipity", urgency=0.3)
        return list(self.queue)

    def next_task(self) -> Optional[IdleTask]:
        if not self.queue or self.budget <= 0:
            return None
        task = self.queue.pop(0)
        self.budget = max(0.0, self.budget - 0.15)
        return task
