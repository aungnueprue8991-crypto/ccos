"""N4 adversarial tests."""
import pytest
from hermes.shell import Hermes
from constitution.schemas.rsi import RSIStatus
from constitution.schemas.capability import CapabilityLifecycle
from capabilities.adapters.echo import EchoAdapter

def test_unauthorized_promotion_without_verify(tmp_path):
    h = Hermes(tmp_path)
    p = h.n4.propose("x", "h", {"a": 1})
    c = h.n4.materialize_candidate(p.proposal_id)
    def weak(impl):
        return {"success_rate": 0.1, "latency_norm": 0.9, "accuracy": 0.1, "safety": 0.1}
    exp = h.n4.run_experiment(c.candidate_id, weak)
    assert exp.status == RSIStatus.REJECTED
    with pytest.raises(PermissionError):
        h.n4.request_promotion(exp.experiment_id)

def test_n1_n3_regression_still_holds(tmp_path):
    h = Hermes(tmp_path)
    m = h.fabric.register_adapter(EchoAdapter())
    with pytest.raises(PermissionError):
        h.registry.transition(m.capability_id, CapabilityLifecycle.ACTIVE, reason="x", authorized_by="y")
