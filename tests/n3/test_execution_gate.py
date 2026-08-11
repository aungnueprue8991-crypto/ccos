"""N3 Execution Gate tests."""
import pytest
from hermes.shell import Hermes
from constitution.schemas.invocation import InvocationEnvelope
from capabilities.adapters.echo import EchoAdapter
from capabilities.adapters.runtime.process_adapter import ProcessAdapter
from capabilities.adapters.runtime.filesystem_adapter import FilesystemAdapter

def _activate(h, adapter):
    outcome = h.fabric.full_lifecycle(adapter)
    assert outcome.activated, outcome.errors
    return outcome.capability_id, adapter

def test_authorization_before_effect(tmp_path):
    h = Hermes(tmp_path)
    cap_id, adapter = _activate(h, EchoAdapter())
    inv = InvocationEnvelope(
        capability_id=cap_id, issuer="agent:tester", intent_id="intent-1",
        input_payload={"message": "n3-hello"}, provenance=["test"],
    )
    decision, result = h.invoker.invoke(inv, adapter)
    assert decision.allowed and result.success
    assert result.output["echo"] == "n3-hello"

def test_deny_inactive_capability(tmp_path):
    h = Hermes(tmp_path)
    m = h.fabric.register_adapter(EchoAdapter())
    inv = InvocationEnvelope(capability_id=m.capability_id, issuer="agent:x",
                             input_payload={"message": "nope"})
    decision, result = h.invoker.invoke(inv, EchoAdapter())
    assert not decision.allowed and not result.success

def test_deny_missing_issuer(tmp_path):
    h = Hermes(tmp_path)
    cap_id, adapter = _activate(h, EchoAdapter())
    inv = InvocationEnvelope(capability_id=cap_id, issuer="", input_payload={"message": "x"})
    decision, result = h.invoker.invoke(inv, adapter)
    assert not decision.allowed

def test_process_requires_intent(tmp_path):
    h = Hermes(tmp_path)
    outcome = h.fabric.full_lifecycle(ProcessAdapter(), execute_payload={"cmd": "date"})
    inv = InvocationEnvelope(
        capability_id=outcome.capability_id, issuer="agent:ops",
        input_payload={"cmd": "date"},
    )
    decision, result = h.invoker.invoke(inv, ProcessAdapter())
    assert not decision.allowed
    assert "intent" in decision.reason.lower()

def test_filesystem_confined(tmp_path):
    h = Hermes(tmp_path)
    root = tmp_path / "fs"
    root.mkdir()
    (root / "note.txt").write_text("civilization")
    adapter = FilesystemAdapter(root=root)
    outcome = h.fabric.full_lifecycle(adapter, execute_payload={"path": "note.txt"})
    inv = InvocationEnvelope(
        capability_id=outcome.capability_id, issuer="agent:reader", intent_id="intent-fs",
        input_payload={"path": "note.txt"},
    )
    decision, result = h.invoker.invoke(inv, adapter)
    assert decision.allowed and result.success
    assert "civilization" in result.output["preview"]
