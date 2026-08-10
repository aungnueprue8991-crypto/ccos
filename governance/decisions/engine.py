"""Governance control plane (blueprint §22).

Proposal → Policy Evaluation → Authorization → Risk → Independent Verification → Decision → Execution → Audit
"""

from __future__ import annotations
from typing import Optional
from constitution.schemas.governance import Proposal, Decision, ProposalStatus
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class GovernanceEngine:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._proposals: dict[str, Proposal] = {}
        self._decisions: dict[str, Decision] = {}

    def submit(self, proposal: Proposal) -> Proposal:
        proposal.status = ProposalStatus.SUBMITTED
        self._proposals[proposal.proposal_id] = proposal
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="governance.proposal.submitted",
                    producer_id="ccos.governance",
                    payload={
                        "proposal_id": proposal.proposal_id,
                        "type": proposal.proposal_type,
                        "title": proposal.title,
                        "proposer": proposal.proposer,
                    },
                )
            )
        return proposal

    def decide(
        self,
        proposal_id: str,
        decision_maker: str,
        outcome: str,
        rationale: str = "",
        evidence: list[str] | None = None,
    ) -> Decision:
        prop = self._proposals[proposal_id]
        decision = Decision(
            proposal_id=proposal_id,
            decision_maker=decision_maker,
            outcome=outcome,
            rationale=rationale,
            evidence_considered=evidence or prop.evidence_refs,
        )
        self._decisions[decision.decision_id] = decision
        prop.decision_ref = decision.decision_id
        prop.status = (
            ProposalStatus.APPROVED if outcome == "APPROVED" else ProposalStatus.REJECTED
        )
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="governance.decision",
                    producer_id="ccos.governance",
                    payload={
                        "decision_id": decision.decision_id,
                        "proposal_id": proposal_id,
                        "outcome": outcome,
                        "decision_maker": decision_maker,
                    },
                )
            )
        return decision
