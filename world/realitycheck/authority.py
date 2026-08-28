"""RealityAuthority — public API for NEXUS; writes evidence chain when ledger available."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from world.realitycheck.compiler import ExperimentCompiler
from world.realitycheck.registry import ClaimRegistry
from world.realitycheck.types import Claim, ExperimentSpec, RealityVerdict
from world.realitycheck.verdict import VerdictEngine
from world.realitycheck.protocol import ProtocolRunner, ProtocolChecklist
from world.realitycheck.verifiers import (
    AdversarialVerifier,
    BenchmarkEngine,
    CodeVerifier,
    DependencyVerifier,
    ReproductionEngine,
    SourceValidator,
)


class RealityAuthority:
    """NEXUS proposes; RealityAuthority decides what counts as knowledge."""

    def __init__(self, ledger=None):
        self.registry = ClaimRegistry()
        self.compiler = ExperimentCompiler(self.registry)
        self.verdict_engine = VerdictEngine()
        self.code = CodeVerifier()
        self.repro = ReproductionEngine()
        self.adv = AdversarialVerifier()
        self.source = SourceValidator()
        self.bench = BenchmarkEngine()
        self.deps = DependencyVerifier()
        self.ledger = ledger
        self.protocol = ProtocolRunner()
        self.protocol_history: list = []

    def submit_claim(
        self,
        statement: str,
        domain: str = "general",
        metrics: Optional[Dict[str, float]] = None,
        baseline: Optional[Dict[str, float]] = None,
        model_confidence: float = 0.0,
    ) -> tuple[Claim, ExperimentSpec]:
        claim, spec = self.compiler.compile(
            statement,
            domain=domain,
            metrics=metrics,
            baseline=baseline,
            model_confidence=model_confidence,
        )
        self._ledger_event("realitycheck.claim_registered", claim.to_dict())
        return claim, spec

    def verify(
        self,
        claim: Claim,
        spec: ExperimentSpec,
        run_fn: Optional[Callable[[], Dict[str, float]]] = None,
        known_sources: Optional[List[str]] = None,
        seed: int = 0,
    ) -> RealityVerdict:
        code_r = self.code.verify(spec, run_fn=run_fn) if run_fn else None
        repro_r = None
        adv_r = None
        if run_fn and code_r and code_r.passed:
            repro_r = self.repro.reproduce(run_fn, n=spec.n_trials)
            adv_r = self.adv.probe(code_r.measurements, spec.adversarial_tests, seed=seed)
        src_r = self.source.validate(claim.statement, known_sources=known_sources)
        bench_r = None
        if code_r and claim.baseline:
            bench_r = self.bench.run(code_r.measurements, claim.baseline)

        verdict = self.verdict_engine.decide(
            claim, code=code_r, reproduction=repro_r, adversarial=adv_r, source=src_r, benchmark=bench_r
        )
        self.registry.attach_verdict(verdict)
        self._ledger_event("realitycheck.verdict", verdict.to_dict())
        return verdict

    def check_memory_compression_claim(
        self,
        compression_ratio: float,
        accuracy_loss: float,
        statement: str | None = None,
    ) -> RealityVerdict:
        statement = statement or (
            "Compression reduces memory storage by 60% while retrieval accuracy decreases < 2%."
        )
        claim, spec = self.submit_claim(
            statement,
            domain="memory",
            metrics={"compression_ratio_min": 0.60, "accuracy_loss_max": 0.02},
            baseline={"storage": 1.0, "accuracy": 1.0},
            model_confidence=0.99,
        )

        def run() -> Dict[str, float]:
            return {
                "compression_ratio": compression_ratio,
                "accuracy_loss": accuracy_loss,
                "retrieval_fidelity": 1.0 - accuracy_loss,
            }

        return self.verify(claim, spec, run_fn=run, seed=1)

    def protocol_check(
        self,
        claim_text: str,
        proposition: str,
        minimum_evidence: str,
        run_fn,
        expected_fn,
        *,
        artifact: str = "",
        falsify_fn=None,
        model_confidence: float = 0.0,
        reproduce: bool = True,
    ) -> ProtocolChecklist:
        cl = self.protocol.run(
            claim_text=claim_text,
            falsifiable_proposition=proposition,
            minimum_evidence=minimum_evidence,
            run_fn=run_fn,
            expected_fn=expected_fn,
            artifact=artifact,
            falsify_fn=falsify_fn,
            model_confidence=model_confidence,
            reproduce=reproduce,
        )
        self.protocol_history.append(cl)
        self._ledger_event("realitycheck.protocol", cl.to_dict())
        return cl

    def knowledge_claims(self) -> List[Claim]:
        return self.registry.knowledge_only()

    def _ledger_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.ledger is None:
            return
        try:
            if hasattr(self.ledger, "append"):
                self.ledger.append({"type": event_type, "payload": payload})
            elif hasattr(self.ledger, "record"):
                self.ledger.record(event_type, payload)
        except Exception:
            pass
