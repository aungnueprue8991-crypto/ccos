"""Serendipity Layer A (drive budget + tokens) and Layer B (structural gate)."""

from __future__ import annotations

from nexus.serendipity.engine import SerendipityEngine
from nexus.types import ThoughtKind


def test_budget_rises_with_novelty_hunger():
    eng = SerendipityEngine(seed=1)
    low = eng.compute_budget(novelty_hunger=0.0, resource_pressure=0.5, surprise_crisis=0.0)
    high = eng.compute_budget(novelty_hunger=1.0, resource_pressure=0.0, surprise_crisis=0.0)
    assert high > low
    assert eng.state.min_b <= high <= eng.state.max_b


def test_crisis_suppresses_budget():
    eng = SerendipityEngine(seed=1, base_budget=0.25)
    calm = eng.compute_budget(novelty_hunger=0.5, surprise_crisis=0.0)
    crisis = eng.compute_budget(novelty_hunger=0.5, surprise_crisis=1.0)
    assert crisis < calm


def test_consolidation_boosts_budget():
    eng = SerendipityEngine(seed=1, base_budget=0.15)
    normal = eng.compute_budget(novelty_hunger=0.3, consolidation_phase=False)
    dream = eng.compute_budget(novelty_hunger=0.3, consolidation_phase=True)
    assert dream >= normal


def test_token_quota_exhaustion():
    eng = SerendipityEngine(seed=0, base_budget=1.0, tokens_per_epoch=2, epoch_len=100)
    clusters = [
        "thermal_equilibration_flow",
        "resource_pool_equalization",
        "selection_fitness_search",
        "compression_sparsity_code",
    ]
    emits = 0
    for _ in range(10):
        out = eng.maybe_link(
            clusters,
            novelty_hunger=1.0,
            resource_pressure=0.0,
            surprise_crisis=0.0,
        )
        emits += len(out)
    assert emits <= 2
    assert eng.state.tokens_left == 0


def test_structural_gate_prefers_relevant_unexpected():
    eng = SerendipityEngine(seed=2, structural_tau=0.3, min_lexical_distance=0.2)
    ranked = eng.rank_candidates(
        [
            "thermal_equilibration_confirmed",
            "resource_equalization_flow",
            "thermal_equilibration_confirmed",
        ]
    )
    assert isinstance(ranked, list)
    if ranked:
        top = ranked[0]
        assert top.structural_similarity >= eng.structural_tau
        assert top.lexical_distance >= eng.min_lexical_distance
        assert top.score == top.lexical_distance * top.structural_similarity


def test_identical_clusters_low_lexical():
    eng = SerendipityEngine(seed=3)
    d = eng.lexical_distance("heat flow equilibrium", "heat flow equilibrium")
    assert d == 0.0


def test_emit_has_payload_metrics():
    eng = SerendipityEngine(seed=4, base_budget=1.0, tokens_per_epoch=5)
    clusters = [
        "thermal_conservation_flow",
        "resource_equalization_constraint",
        "selection_search_landscape",
    ]
    got = []
    for _ in range(20):
        got = eng.maybe_link(
            clusters,
            novelty_hunger=1.0,
            resource_pressure=0.0,
            surprise_crisis=0.0,
        )
        if got:
            break
    if got:
        t = got[0]
        assert t.kind == ThoughtKind.SERENDIPITY
        assert "score" in t.payload
        assert "structural_similarity" in t.payload
        assert "budget" in t.payload
