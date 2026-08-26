"""Self-Optimization Loop — profile → bottleneck → candidate → sandbox → adopt/reject.

Never promotes self-modification without benchmark evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class OptimizationProposal:
    name: str
    bottleneck: str
    hypothesis: str
    metric_before: float
    metric_after: Optional[float] = None
    adopted: bool = False
    evidence: List[str] = field(default_factory=list)


class SelfOptimizationLoop:
    def __init__(self, min_improvement: float = 0.05):
        self.min_improvement = min_improvement
        self.history: List[OptimizationProposal] = []

    def propose(self, bottleneck: str, hypothesis: str, metric_before: float) -> OptimizationProposal:
        p = OptimizationProposal(
            name=f"opt_{len(self.history)+1}",
            bottleneck=bottleneck,
            hypothesis=hypothesis,
            metric_before=metric_before,
        )
        self.history.append(p)
        return p

    def evaluate(
        self,
        proposal: OptimizationProposal,
        sandbox_fn: Callable[[], float],
    ) -> OptimizationProposal:
        """sandbox_fn returns metric (higher is better)."""
        try:
            after = float(sandbox_fn())
        except Exception as e:
            proposal.evidence.append(f"sandbox_error:{e}")
            proposal.adopted = False
            return proposal
        proposal.metric_after = after
        delta = after - proposal.metric_before
        proposal.evidence.append(f"delta={delta:.4f}")
        if delta >= self.min_improvement:
            proposal.adopted = True
            proposal.evidence.append("ADOPT")
        else:
            proposal.adopted = False
            proposal.evidence.append("REJECT")
        return proposal
