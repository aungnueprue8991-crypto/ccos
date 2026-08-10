"""Policy Evaluator — simple rule engine against proposals and actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from constitution.schemas.governance import Proposal
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class PolicyResult:
    allowed: bool
    policy_id: str
    reason: str


class PolicyEvaluator:
    """Evaluates proposals against registered policy functions."""

    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._policies: Dict[str, Callable[[Proposal], PolicyResult]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        def no_unverified_promotion(p: Proposal) -> PolicyResult:
            if p.proposal_type == "capability_promotion":
                if not p.evidence_refs:
                    return PolicyResult(False, "POL-001", "promotion requires evidence_refs")
            return PolicyResult(True, "POL-001", "ok")

        def attributable_proposer(p: Proposal) -> PolicyResult:
            if not p.proposer:
                return PolicyResult(False, "POL-002", "proposer required (CCOS-010)")
            return PolicyResult(True, "POL-002", "ok")

        self._policies["POL-001"] = no_unverified_promotion
        self._policies["POL-002"] = attributable_proposer

    def register(self, policy_id: str, fn: Callable[[Proposal], PolicyResult]) -> None:
        self._policies[policy_id] = fn

    def evaluate(self, proposal: Proposal) -> List[PolicyResult]:
        results = []
        for pid, fn in self._policies.items():
            result = fn(proposal)
            results.append(result)
            if self.ledger:
                self.ledger.append(
                    EventEnvelope(
                        event_type="governance.policy.evaluated",
                        producer_id="governance.policies",
                        payload={
                            "proposal_id": proposal.proposal_id,
                            "policy_id": result.policy_id,
                            "allowed": result.allowed,
                            "reason": result.reason,
                        },
                    )
                )
        return results

    def all_allowed(self, proposal: Proposal) -> bool:
        return all(r.allowed for r in self.evaluate(proposal))
