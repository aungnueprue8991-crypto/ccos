"""Autonomous Research Engine — internal research queue without user prompt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from nexus.epistemic.curiosity import CuriosityAllocator, CuriosityScore
from nexus.inspiration.engine import InspirationEngine


@dataclass
class ResearchItem:
    question: str
    priority: float
    domain: str = "general"
    status: str = "queued"  # queued|active|done
    notes: List[str] = field(default_factory=list)


class AutonomousResearchEngine:
    def __init__(self):
        self.queue: List[ResearchItem] = []
        self.curiosity = CuriosityAllocator()
        self.inspiration = InspirationEngine()

    def enqueue_from_gaps(
        self,
        unresolved_questions: List[str],
        contradictions: int = 0,
        capability_gaps: Optional[List[str]] = None,
    ) -> List[ResearchItem]:
        items = []
        for i, q in enumerate(unresolved_questions):
            cs = self.curiosity.score(
                q,
                expected_learning=0.6,
                usefulness=0.7,
                uncertainty=0.8,
                cost=1.0 + 0.1 * i,
            )
            items.append(ResearchItem(question=q, priority=cs.value, domain="general"))
        for g in capability_gaps or []:
            items.append(
                ResearchItem(
                    question=f"How to acquire capability: {g}?",
                    priority=0.8,
                    domain="capability",
                )
            )
        if contradictions > 0:
            items.append(
                ResearchItem(
                    question="Resolve open contradictions via boundary conditions",
                    priority=0.75 + 0.05 * min(contradictions, 5),
                    domain="epistemic",
                )
            )
        self.queue.extend(items)
        self.queue.sort(key=lambda x: x.priority, reverse=True)
        return items

    def next_item(self) -> Optional[ResearchItem]:
        for it in self.queue:
            if it.status == "queued":
                it.status = "active"
                return it
        return None

    def explore_cross_domain(self, domain: str, problem: str) -> List[Dict[str, Any]]:
        cands = self.inspiration.inspire(domain, problem, k=3)
        return [
            {"idea": c.idea, "source": c.source_domain, "sim": c.structural_sim}
            for c in cands
        ]
