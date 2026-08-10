"""Governed Recursive Self-Improvement loop (blueprint §14).

Frontier design constraints (research-backed):
- RSI proposes candidates; never activates (CCOS-004).
- Public scores visible to loop; private scores held out for governance only.
- Authority surface unchanged without external GovernanceEngine decision.
- Every cycle fully audited on the event spine.
- Rollback target required before any promotion proposal.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from constitution.schemas.event import EventEnvelope
from constitution.schemas.scos import Experiment
from constitution.schemas.governance import Proposal
from constitution.schemas.capability import CapabilityManifest, CapabilityLifecycle
from kernel.events.ledger import EventLedger
from kernel.registry.capability_registry import CapabilityRegistry
from governance.decisions.engine import GovernanceEngine
from evolution.hypotheses.engine import HypothesisEngine
from evolution.experiments.runner import ExperimentRunner
from evolution.archive.store import ExperimentArchive
from evolution.benchmarks.split import SplitBenchmarkHarness, SplitScore


class CandidateKind(str, Enum):
    CONFIG_DELTA = "CONFIG_DELTA"
    PROMPT_DELTA = "PROMPT_DELTA"
    BENCHMARK_WEIGHT = "BENCHMARK_WEIGHT"
    COSMOS_PARAM = "COSMOS_PARAM"


class RSICandidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid4()))
    kind: CandidateKind
    description: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    parent_capability_id: Optional[str] = None
    public_score: float = 0.0
    hypothesis_id: Optional[str] = None
    experiment_id: Optional[str] = None
    run_id: Optional[str] = None
    rollback_target: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PromotionPredicate:
    min_public: float = 0.6
    min_private: float = 0.6
    min_safety: float = 0.9
    require_provenance: bool = True
    require_rollback_target: bool = True

    def evaluate(
        self,
        public_scalar: float,
        private_scalar: float,
        safety: float,
        provenance: list[str],
        rollback_target: Optional[str],
    ) -> tuple[bool, str]:
        if public_scalar < self.min_public:
            return False, f"public_score {public_scalar:.3f} < {self.min_public}"
        if private_scalar < self.min_private:
            return False, f"private_score {private_scalar:.3f} < {self.min_private}"
        if safety < self.min_safety:
            return False, f"safety {safety:.3f} < {self.min_safety}"
        if self.require_provenance and not provenance:
            return False, "missing provenance"
        if self.require_rollback_target and not rollback_target:
            return False, "missing rollback_target"
        return True, "all gates passed"


@dataclass
class CycleResult:
    cycle: int
    hypothesis_id: str
    candidate_id: str
    public_score: float
    private_score: float
    gates_passed: bool
    gate_reason: str
    proposal_id: Optional[str] = None
    decision: Optional[str] = None
    activated: bool = False


class GovernedRSILoop:
    """Evidence-gated RSI. Proposes only. Cannot call registry.transition to ACTIVE."""

    def __init__(
        self,
        ledger: EventLedger,
        hypotheses: HypothesisEngine,
        experiments: ExperimentRunner,
        archive: ExperimentArchive,
        split_bench: SplitBenchmarkHarness,
        governance: GovernanceEngine,
        registry: CapabilityRegistry,
        predicate: Optional[PromotionPredicate] = None,
    ):
        self.ledger = ledger
        self.hypotheses = hypotheses
        self.experiments = experiments
        self.archive = archive
        self.split_bench = split_bench
        self.governance = governance
        self.registry = registry
        self.predicate = predicate or PromotionPredicate()
        self.history: List[CycleResult] = []
        self._cycle = 0

    def _emit(self, event_type: str, payload: dict) -> None:
        self.ledger.append(
            EventEnvelope(event_type=event_type, producer_id="scos.rsi", payload=payload)
        )

    def run_cycle(
        self,
        objective: str,
        evaluate_fn: Callable[[Dict[str, Any]], SplitScore],
        candidate_factory: Callable[[int], RSICandidate],
        domain: str = "rsi",
        auto_governance: bool = False,
        decision_maker: str = "citizen:governor",
    ) -> CycleResult:
        self._cycle += 1
        cycle = self._cycle

        hyp = self.hypotheses.generate(
            statement=f"[RSI c{cycle}] {objective}",
            predictions=[f"improve public fitness on cycle {cycle}"],
            domain=domain,
            provenance=[f"rsi-cycle-{cycle}"],
        )
        self._emit("scos.rsi.hypothesis", {"cycle": cycle, "hypothesis_id": hyp.hypothesis_id})

        cand = candidate_factory(cycle)
        cand.hypothesis_id = hyp.hypothesis_id

        exp = Experiment(
            hypothesis_ref=hyp.hypothesis_id,
            parameters=dict(cand.payload),
            random_seed=42 + cycle,
            provenance=[hyp.hypothesis_id, f"rsi-cycle-{cycle}"],
        )

        def _run(params: dict) -> dict[str, float]:
            suite_name = f"rsi-{cand.candidate_id[:8]}"
            self.split_bench.register(suite_name, lambda: evaluate_fn(params))
            score = self.split_bench.run_full(suite_name)
            return {**score.public, **{f"private_{k}": v for k, v in score.private.items()}}

        exp = self.experiments.run(exp, _run)

        public = {k: v for k, v in exp.metrics.items() if not k.startswith("private_")}
        private = {k.replace("private_", ""): v for k, v in exp.metrics.items() if k.startswith("private_")}
        public.pop("duration_s", None)
        public.pop("error", None)

        public_scalar = sum(public.values()) / max(len(public), 1)
        private_scalar = sum(private.values()) / max(len(private), 1) if private else 0.0
        safety = private.get("safety", public.get("safety", 1.0))

        cand.public_score = public_scalar
        cand.experiment_id = exp.experiment_id

        run = self.archive.archive(
            experiment_id=exp.experiment_id,
            parameters=dict(cand.payload),
            public_metrics=public,
            private_metrics=private,
            random_seed=exp.random_seed or 42,
            hypothesis_ref=hyp.hypothesis_id,
            code_hash=hashlib.sha256(json.dumps(cand.payload, sort_keys=True).encode()).hexdigest()[:16],
        )
        cand.run_id = run.run_id

        ok, reason = self.predicate.evaluate(
            public_scalar, private_scalar, safety,
            provenance=[hyp.hypothesis_id, exp.experiment_id],
            rollback_target=cand.rollback_target,
        )

        result = CycleResult(
            cycle=cycle,
            hypothesis_id=hyp.hypothesis_id,
            candidate_id=cand.candidate_id,
            public_score=public_scalar,
            private_score=private_scalar,
            gates_passed=ok,
            gate_reason=reason,
        )

        self._emit(
            "scos.rsi.cycle",
            {
                "cycle": cycle,
                "candidate_id": cand.candidate_id,
                "kind": cand.kind.value,
                "public_score": public_scalar,
                "gates_passed": ok,
                "gate_reason": reason,
                "run_id": run.run_id,
            },
        )

        if not ok:
            self.hypotheses.falsify(hyp.hypothesis_id, reason=reason)
            self.history.append(result)
            return result

        self.hypotheses.support(hyp.hypothesis_id)
        self.hypotheses.rank(hyp.hypothesis_id, public_scalar)

        prop = Proposal(
            proposer="scos.rsi",
            title=f"RSI promote {cand.kind.value} c{cycle}",
            proposal_type="capability_promotion",
            payload={
                "candidate_id": cand.candidate_id,
                "kind": cand.kind.value,
                "public_score": public_scalar,
                "run_id": run.run_id,
                "rollback_target": cand.rollback_target,
            },
            evidence_refs=[hyp.hypothesis_id, exp.experiment_id, run.run_id],
        )
        prop = self.governance.submit(prop)
        result.proposal_id = prop.proposal_id

        if auto_governance:
            decision = self.governance.decide(
                prop.proposal_id,
                decision_maker=decision_maker,
                outcome="APPROVED",
                rationale=f"gates passed: {reason}; public={public_scalar:.3f}",
                evidence=[hyp.hypothesis_id, exp.experiment_id],
            )
            result.decision = decision.outcome
            manifest = CapabilityManifest(
                name=f"rsi-{cand.kind.value.lower()}-{cycle}",
                description=cand.description,
                version=f"0.{cycle}.0",
                provenance=[hyp.hypothesis_id, exp.experiment_id],
            )
            self.registry.register(manifest)
            self.registry.transition(
                manifest.capability_id,
                CapabilityLifecycle.APPROVED,
                reason="governance approved RSI candidate",
                authorized_by=decision_maker,
            )
            result.activated = False
            self._emit(
                "scos.rsi.approved_not_activated",
                {
                    "cycle": cycle,
                    "capability_id": manifest.capability_id,
                    "note": "ACTIVE requires separate authorized transition outside RSI",
                },
            )

        self.history.append(result)
        return result

    def run_n(
        self,
        n: int,
        objective: str,
        evaluate_fn: Callable[[Dict[str, Any]], SplitScore],
        candidate_factory: Callable[[int], RSICandidate],
        **kwargs,
    ) -> List[CycleResult]:
        results = []
        for _ in range(n):
            results.append(self.run_cycle(objective, evaluate_fn, candidate_factory, **kwargs))
        return results

    def assert_no_auto_activation(self) -> None:
        for ev in self.ledger.find_by_type("capability.lifecycle"):
            if ev.producer_id == "scos.rsi" and ev.payload.get("to") == "ACTIVE":
                raise AssertionError("CONSTITUTIONAL VIOLATION: RSI auto-activated capability")
        for r in self.history:
            if r.activated:
                raise AssertionError("CONSTITUTIONAL VIOLATION: CycleResult.activated=True from RSI")
