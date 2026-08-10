"""SCOS Promotion path — proposes only; never auto-activates (CCOS-004)."""

from __future__ import annotations
from typing import Optional
from constitution.schemas.scos import PromotionCandidate, Experiment
from constitution.schemas.capability import CapabilityManifest, CapabilityLifecycle
from constitution.schemas.governance import Proposal
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger
from kernel.registry.capability_registry import CapabilityRegistry
from governance.decisions.engine import GovernanceEngine


class PromotionPipeline:
    def __init__(
        self,
        ledger: Optional[EventLedger] = None,
        registry: Optional[CapabilityRegistry] = None,
        governance: Optional[GovernanceEngine] = None,
    ):
        self.ledger = ledger
        self.registry = registry
        self.governance = governance
        self._candidates: dict[str, PromotionCandidate] = {}

    def propose_candidate(
        self,
        manifest: CapabilityManifest,
        experiment: Experiment,
        benchmarks: dict[str, float],
    ) -> PromotionCandidate:
        cand = PromotionCandidate(
            capability_manifest_ref=manifest.capability_id,
            experiment_refs=[experiment.experiment_id],
            benchmark_results=benchmarks,
            status="CANDIDATE",
            lineage=manifest.provenance,
        )
        self._candidates[cand.candidate_id] = cand
        if self.registry:
            self.registry.register(manifest)
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="scos.promotion.candidate",
                    producer_id="scos.promotion",
                    payload={
                        "candidate_id": cand.candidate_id,
                        "capability": manifest.name,
                        "benchmarks": benchmarks,
                    },
                )
            )
        return cand

    def request_governance_approval(self, candidate_id: str, proposer: str) -> Proposal:
        cand = self._candidates[candidate_id]
        cand.status = "PROPOSED"
        prop = Proposal(
            proposer=proposer,
            title=f"Promote capability {cand.capability_manifest_ref}",
            proposal_type="capability_promotion",
            payload={"candidate_id": candidate_id},
            evidence_refs=cand.experiment_refs,
        )
        if self.governance:
            return self.governance.submit(prop)
        return prop
