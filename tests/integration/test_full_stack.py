"""Integration tests across all major planes."""

from constitution.schemas.scos import Experiment
from constitution.schemas.capability import CapabilityLifecycle
from hermes.shell import Hermes


def test_full_stack_smoke(tmp_path):
    h = Hermes(tmp_path)
    intent = h.submit_intent("test", "integration")
    ev = h.evidence.ingest_observation("claim", "src")
    ev = h.evidence.validate(ev.evidence_id, 0.9)
    e = h.knowledge.add_entity("X")
    h.knowledge.add_relation(e.entity_id, e.entity_id, "self", provenance=[ev.evidence_id], confidence=0.8)
    h.beliefs.assert_belief("X exists", [ev.evidence_id], 0.9)
    h.world_model.snapshot({"x": 1}, provenance=[ev.evidence_id])
    h.experience.record("act", "ok", True, intent_id=intent.intent_id)
    org = h.organizations.create("Lab")
    agent, citizen = h.population.spawn_citizen("a1", org.name, "researcher")
    assert h.population.size() == 1
    hyp = h.hypotheses.generate("H", provenance=[ev.evidence_id])
    h.hypotheses.rank(hyp.hypothesis_id, 0.8)
    ex = Experiment(parameters={"n": 1}, random_seed=1, provenance=[ev.evidence_id])
    h.experiments.run(ex, lambda p: {"accuracy": 1.0})
    h.benchmarks.register("t", lambda: {"accuracy": 1.0, "safety": 1.0})
    assert h.benchmarks.run("t").passed
    h.cosmos.spawn("e")
    h.cosmos.tick(2)
    assert h.cosmos.measure()["tick"] == 2.0
    assert h.health().status == "healthy"
    assert h.ledger.verify_chain()
    assert h.status()["chain_valid"] is True


def test_policy_blocks_empty_promotion(tmp_path):
    h = Hermes(tmp_path)
    from constitution.schemas.governance import Proposal
    p = Proposal(proposer="x", title="t", proposal_type="capability_promotion", evidence_refs=[])
    assert not h.policies.all_allowed(p)
