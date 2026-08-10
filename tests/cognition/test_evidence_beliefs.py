"""COG unit tests."""
from hermes.shell import Hermes
from constitution.schemas.event import EpistemicStatus

def test_evidence_pipeline_states(tmp_path):
    h = Hermes(tmp_path)
    ev = h.evidence.ingest_observation("sky is blue", "sensor-1")
    assert ev.epistemic_status == EpistemicStatus.UNVERIFIED
    ev = h.evidence.validate(ev.evidence_id, 0.85, methodology="vision")
    assert ev.epistemic_status == EpistemicStatus.SUPPORTED
    ev = h.evidence.corroborate(ev.evidence_id, ["s2", "s3"])
    assert ev.epistemic_status == EpistemicStatus.CORROBORATED

def test_belief_revision(tmp_path):
    h = Hermes(tmp_path)
    ev = h.evidence.ingest_observation("claim", "src")
    h.evidence.validate(ev.evidence_id, 0.8)
    b = h.beliefs.assert_belief("claim holds", [ev.evidence_id], 0.8)
    b2 = h.beliefs.revise(b.belief_id, 0.4, reason="new data")
    assert b2.revised_from == b.belief_id and b2.confidence == 0.4

def test_world_model_snapshot(tmp_path):
    h = Hermes(tmp_path)
    s = h.world_model.snapshot({"temp": 20.0}, provenance=["e1"])
    assert h.world_model.current().state_id == s.state_id
    assert h.world_model.predict({"temp": 25.0})["temp"] == 25.0
