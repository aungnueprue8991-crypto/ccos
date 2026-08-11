"""N2 Network Fabric tests."""
from pathlib import Path
from kernel.network.fabric import NetworkFabric
from constitution.schemas.event import EventEnvelope

def test_provision_and_sync(tmp_path):
    fabric = NetworkFabric()
    a = fabric.create_node("alpha", tmp_path / "a")
    b = fabric.create_node("beta", tmp_path / "b")
    fabric.provision_mesh([a, b])
    a.append_local(EventEnvelope(
        event_type="test.event", producer_id=a.identity.node_id, payload={"x": 1},
    ))
    resp = fabric.sync(a.identity.node_id, b.identity.node_id)
    assert resp.action.value in ("APPEND", "IDEMPOTENT_ACCEPT")
    assert b.ledger.verify_chain()
    assert a.ledger.verify_chain()

def test_invalid_signature_rejected(tmp_path):
    fabric = NetworkFabric()
    a = fabric.create_node("alpha", tmp_path / "a")
    b = fabric.create_node("beta", tmp_path / "b")
    fabric.provision_mesh([a, b])
    req = a.build_push_request(b.identity.node_id)
    req.signature = "deadbeef" * 8
    resp = b.handle_request(req)
    assert resp.action.value == "REJECT"

def test_head_info(tmp_path):
    fabric = NetworkFabric()
    a = fabric.create_node("alpha", tmp_path / "a")
    h = a.head()
    assert h.node_id == a.identity.node_id
    assert h.chain_valid
