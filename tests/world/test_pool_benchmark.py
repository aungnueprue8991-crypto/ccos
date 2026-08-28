"""Pool efficiency benchmark + RealityCheck integration."""

from __future__ import annotations

from world.benchmarks.pool_efficiency import PoolEfficiencyBenchmark, run_pool_efficiency_benchmark
from world.benchmarks.lateral_inhibition import competitive_select
from world.realitycheck.authority import RealityAuthority
from world.realitycheck.types import VerdictKind


def test_pool_benchmark_runs():
    r = PoolEfficiencyBenchmark(n_ops=40).run()
    assert r.n_ops == 40
    assert r.naive_seconds > 0
    assert r.pooled_seconds > 0
    assert "compression_ratio" in r.as_realitycheck_metrics()


def test_lateral_inhibition_wta():
    step = competitive_select([0.1, 0.9, 0.2], soft=False, steps=10)
    assert step.winner_index == 1
    assert step.activations[1] >= step.activations[0]


def test_hypothesis_tested_with_real_run_fn():
    auth = RealityAuthority()
    claim, spec = auth.submit_claim(
        "Connection reuse reduces open cost by >= 30% while error rate increases < 2%.",
        domain="computing",
        metrics={"compression_ratio_min": 0.30, "accuracy_loss_max": 0.02},
        model_confidence=0.99,
    )
    v0 = auth.verify(claim, spec, run_fn=None)
    assert v0.kind not in (VerdictKind.IMPLEMENTATION_VERIFIED, VerdictKind.REPRODUCTION_VERIFIED)

    v1 = auth.verify(claim, spec, run_fn=lambda: run_pool_efficiency_benchmark(60))
    assert v1.kind in (
        VerdictKind.IMPLEMENTATION_VERIFIED,
        VerdictKind.REPRODUCTION_VERIFIED,
        VerdictKind.FALSIFIED,
        VerdictKind.INCONCLUSIVE,
        VerdictKind.ADVERSARIAL_FAIL,
        VerdictKind.PARTIALLY_SUPPORTED,
    )
    assert v1.measurements
