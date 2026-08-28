"""Abstraction ladder: observation → pattern → mechanism → principle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from nexus.types import Theory


@dataclass
class AbstractionStep:
    level: str
    content: str
    parent: Optional[str] = None


class AbstractionEngine:
    def climb(
        self,
        observations: List[str],
        mechanism: str,
        domain: str = "general",
    ) -> List[AbstractionStep]:
        steps: List[AbstractionStep] = []
        for obs in observations[:5]:
            steps.append(AbstractionStep("observation", obs))
        if observations:
            pattern = f"recurring pattern across {len(observations)} observations in {domain}"
            steps.append(AbstractionStep("pattern", pattern))
        steps.append(AbstractionStep("mechanism", mechanism))
        principle = f"mechanism '{mechanism}' may reduce uncertainty wherever similar structure appears"
        steps.append(AbstractionStep("principle", principle))
        return steps

    def to_theory(
        self,
        mechanism: str,
        evidence_ids: List[str],
        domain: str = "general",
        confidence: float = 0.55,
    ) -> Theory:
        steps = self.climb([], mechanism, domain)
        return Theory(
            mechanism=mechanism,
            boundary_conditions=[f"domain≈{domain}"],
            supporting_evidence=list(evidence_ids),
            abstractions=[s.content for s in steps if s.level in ("pattern", "principle")],
            domain=domain,
            confidence=confidence,
        )
