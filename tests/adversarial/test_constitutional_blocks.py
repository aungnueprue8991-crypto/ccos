"""Adversarial tests — every attack must fail closed."""

import pytest
from constitution.schemas.memory import MemoryRecord, MemoryKind
from constitution.schemas.event import EpistemicStatus
from constitution.schemas.capability import CapabilityManifest, CapabilityLifecycle
from constitution.schemas.governance import Proposal
from hermes.shell import Hermes


def test_memory_rejects_empty_provenance(tmp_path):
    h = Hermes(tmp_path)
    rec = MemoryRecord(
        namespace="scientific", kind=MemoryKind.SCIENTIFIC, content={"x": 1},
        provenance=[], epistemic_status=EpistemicStatus.SUPPORTED, writer="attacker",
    )
    with pytest.raises(PermissionError, match="provenance"):
        h.memory.write(rec)


def test_memory_rejects_unverified_permanent(tmp_path):
    h = Hermes(tmp_path)
    rec = MemoryRecord(
        namespace="scientific", kind=MemoryKind.SCIENTIFIC, content={"x": 1},
        provenance=["e1"], epistemic_status=EpistemicStatus.UNVERIFIED, writer="attacker",
    )
    with pytest.raises(PermissionError, match="unverified"):
        h.memory.write(rec)


def test_belief_requires_evidence(tmp_path):
    h = Hermes(tmp_path)
    with pytest.raises(PermissionError, match="provenance"):
        h.beliefs.assert_belief("false claim", evidence_ids=[], confidence=0.99)


def test_relation_requires_provenance(tmp_path):
    h = Hermes(tmp_path)
    e = h.knowledge.add_entity("A")
    with pytest.raises(PermissionError, match="provenance"):
        h.knowledge.add_relation(e.entity_id, e.entity_id, "self", provenance=[])


def test_capability_cannot_jump_to_active(tmp_path):
    h = Hermes(tmp_path)
    m = CapabilityManifest(name="evil", description="x", version="0.0.1", provenance=["p"])
    h.registry.register(m)
    with pytest.raises(Exception):
        h.registry.transition(m.capability_id, CapabilityLifecycle.ACTIVE, reason="hack", authorized_by="attacker")


def test_policy_blocks_promotion_without_evidence(tmp_path):
    h = Hermes(tmp_path)
    p = Proposal(proposer="x", title="t", proposal_type="capability_promotion", evidence_refs=[])
    assert not h.policies.all_allowed(p)


def test_rsi_cannot_auto_activate(tmp_path):
    from evolution.rsi.loop import GovernedRSILoop, RSICandidate, CandidateKind, PromotionPredicate
    from evolution.archive.store import ExperimentArchive
    from evolution.benchmarks.split import SplitBenchmarkHarness, SplitScore
    h = Hermes(tmp_path)
    archive = ExperimentArchive(h.ledger, tmp_path / "exp.db")
    split = SplitBenchmarkHarness(h.ledger)
    loop = GovernedRSILoop(
        h.ledger, h.hypotheses, h.experiments, archive, split, h.governance, h.registry,
        predicate=PromotionPredicate(min_public=0.0, min_private=0.0, min_safety=0.0),
    )
    def evaluate(params):
        return SplitScore(public={"accuracy": 0.9}, private={"safety": 1.0, "heldout": 0.95})
    def factory(cycle):
        return RSICandidate(kind=CandidateKind.COSMOS_PARAM, description=f"cycle {cycle}",
                            payload={"energy_decay": 0.01 * cycle}, rollback_target="baseline")
    results = loop.run_n(3, "improve cosmos", evaluate, factory, auto_governance=True)
    assert len(results) == 3
    loop.assert_no_auto_activation()
    assert all(not r.activated for r in results)
