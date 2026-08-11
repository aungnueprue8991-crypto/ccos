"""N1 Capability Fabric tests."""
import pytest
from hermes.shell import Hermes
from capabilities.adapters.echo import EchoAdapter
from capabilities.adapters.compute import ComputeAdapter
from constitution.schemas.capability import CapabilityLifecycle

def test_full_lifecycle_echo(tmp_path):
    h = Hermes(tmp_path)
    out = h.fabric.full_lifecycle(EchoAdapter(), execute_payload={"message": "hi"})
    assert out.activated
    assert out.public_score >= 0.5

def test_full_lifecycle_compute(tmp_path):
    h = Hermes(tmp_path)
    out = h.fabric.full_lifecycle(ComputeAdapter(), execute_payload={"op": "mul", "a": 3, "b": 4})
    assert out.activated
    assert out.result and out.result.output.get("result") == 12

def test_illegal_active_transition_blocked(tmp_path):
    h = Hermes(tmp_path)
    m = h.fabric.register_adapter(EchoAdapter())
    with pytest.raises(PermissionError):
        h.registry.transition(m.capability_id, CapabilityLifecycle.ACTIVE, reason="x", authorized_by="y")
