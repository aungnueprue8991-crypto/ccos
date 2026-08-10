"""N4 RSI Evaluation Plane tests."""
import pytest
from hermes.shell import Hermes
from constitution.schemas.rsi import RSIStatus

def _good_eval(impl):
    boost = float(impl.get("boost", 0.1))
    return {"success_rate": 0.80 + boost, "latency_norm": 0.25, "accuracy": 0.80 + boost, "safety": 1.0}

def _bad_eval(impl):
    return {"success_rate": 0.50, "latency_norm": 0.9, "accuracy": 0.50, "safety": 0.5}

def test_n4_proposal_and_candidate(tmp_path):
    h = Hermes(tmp_path)
    p = h.n4.propose("planner", "v2 is better", {"boost": 0.12})
    assert p.status.value == "PROPOSED"
    c = h.n4.materialize_candidate(p.proposal_id)
    assert c.artifact_hash

def test_n4_full_cycle_promotes(tmp_path):
    h = Hermes(tmp_path)
    out = h.n4.run_full_cycle("planner", "boost improves", {"boost": 0.15}, _good_eval)
    assert out["verified"] and out["activated"]
    h.n4.assert_no_direct_mutation()

def test_n4_rejects_weak_candidate(tmp_path):
    h = Hermes(tmp_path)
    out = h.n4.run_full_cycle("planner", "weak", {"boost": -0.3}, _bad_eval)
    assert out["status"] == "REJECTED" and not out["activated"]

def test_n4_rollback(tmp_path):
    h = Hermes(tmp_path)
    out = h.n4.run_full_cycle("planner", "ok", {"boost": 0.12}, _good_eval)
    cand = h.n4.rollback(out["experiment_id"], "citizen:governor", reason="anomaly")
    assert cand.status == RSIStatus.ROLLED_BACK

def test_n4_verifier_detects_forgery(tmp_path):
    h = Hermes(tmp_path)
    p = h.n4.propose("x", "h", {"boost": 0.1})
    c = h.n4.materialize_candidate(p.proposal_id)
    exp = h.n4.run_experiment(c.candidate_id, _good_eval)
    exp.delta_metrics["success_rate"] = 99.0
    v = h.n4.verifier.verify(exp)
    assert v["forgery_detected"] is True

def test_n4_021_no_capability_lifecycle_active(tmp_path):
    h = Hermes(tmp_path)
    h.n4.run_full_cycle("planner", "h", {"boost": 0.1}, _good_eval)
    h.n4.assert_no_direct_mutation()

def test_n4_events_emitted(tmp_path):
    h = Hermes(tmp_path)
    h.n4.run_full_cycle("planner", "h", {"boost": 0.1}, _good_eval)
    types = {e.event_type for e in h.ledger.iter_events()}
    assert "rsi.proposal.created" in types
    assert "deployment.promoted" in types
