"""RealityCheck epistemic authority tests."""

from __future__ import annotations

from world.realitycheck.authority import RealityAuthority
from world.realitycheck.types import VerdictKind


def test_model_confidence_is_not_evidence():
    auth = RealityAuthority()
    claim, spec = auth.submit_claim(
        "Maybe unicorns exist",
        model_confidence=0.99,
    )
    v = auth.verify(claim, spec, run_fn=None)
    assert v.kind in (
        VerdictKind.SPECULATION,
        VerdictKind.HYPOTHESIS,
        VerdictKind.INCONCLUSIVE,
        VerdictKind.SOURCE_SUPPORTED,
    )
    assert "model_confidence_ignored" in " ".join(v.notes)


def test_compression_claim_verified():
    auth = RealityAuthority()
    v = auth.check_memory_compression_claim(compression_ratio=0.72, accuracy_loss=0.013)
    assert v.kind in (
        VerdictKind.IMPLEMENTATION_VERIFIED,
        VerdictKind.REPRODUCTION_VERIFIED,
    )
    assert v.reproduction_pass or v.kind == VerdictKind.IMPLEMENTATION_VERIFIED


def test_compression_claim_falsified():
    auth = RealityAuthority()
    v = auth.check_memory_compression_claim(compression_ratio=0.10, accuracy_loss=0.50)
    assert v.kind == VerdictKind.FALSIFIED


def test_compiler_extracts_metrics():
    auth = RealityAuthority()
    claim, spec = auth.submit_claim(
        "Compression X reduces memory storage by 60% while retrieval accuracy decreases < 2%."
    )
    assert "compression_ratio_min" in claim.metrics or "compression_ratio_min" in spec.success_criteria
    assert spec.procedure
    assert spec.sandbox is True


def test_knowledge_only_filter():
    auth = RealityAuthority()
    auth.check_memory_compression_claim(0.72, 0.01)
    auth.check_memory_compression_claim(0.1, 0.5)
    known = auth.knowledge_claims()
    assert all(
        auth.registry.latest_verdict(c.claim_id).kind.value
        in ("IMPLEMENTATION-VERIFIED", "REPRODUCTION-VERIFIED", "SOURCE-SUPPORTED")
        for c in known
    )
