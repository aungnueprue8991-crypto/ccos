"""NEXUS vNext hierarchical system integration tests."""

from __future__ import annotations

from nexus.discovery.experiment_select import ExperimentSelector
from nexus.epistemic.belief_decay import BeliefDecayEngine
from nexus.epistemic.curiosity import CuriosityAllocator
from nexus.epistemic.evidence_gate import EvidenceGate, BeliefStatus
from nexus.vnext import NexusVNext


def test_evidence_gate_states():
    g = EvidenceGate()
    c = g.register("claim X", predictions=["y"])
    assert c.status == BeliefStatus.UNTESTED
    g.assess(c.claim_id, oracle_accepted=True)
    assert g.claims[c.claim_id].status == BeliefStatus.SUPPORTED


def test_curiosity_and_experiment_eig():
    cur = CuriosityAllocator()
    s = cur.score("topic", 0.8, 0.7, 0.9, cost=2.0)
    assert s.value > 0
    sel = ExperimentSelector()
    cand = sel.score_experiment("e1", {"T1": 0.5, "T2": 0.5}, cost=1.0)
    assert cand.expected_ig > 0
    assert cand.score > 0


def test_belief_decay():
    g = EvidenceGate()
    c = g.register("old")
    g.assess(c.claim_id, oracle_accepted=True)
    c.last_verified = 0
    BeliefDecayEngine(half_life_seconds=1.0).decay(c)
    assert c.confidence < 0.95


def test_vnext_boot_and_discovery():
    nx = NexusVNext(seed=42)
    boot = nx.boot()
    assert boot["status"] == "READY"
    result = nx.run_discovery_from_observation()
    assert result.events >= 1
    assert result.belief_status in (
        "SUPPORTED", "PARTIALLY_SUPPORTED", "INCONCLUSIVE", "FALSIFIED", "UNTESTED"
    )
    assert result.discovery == "thermal_equilibration_confirmed" or result.belief_status == "SUPPORTED"


def test_vnext_idle():
    nx = NexusVNext(seed=1)
    nx.boot()
    out = nx.run_idle_cycle()
    assert "task" in out
