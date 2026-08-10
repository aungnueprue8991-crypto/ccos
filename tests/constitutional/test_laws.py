"""Constitutional invariant smoke tests."""

from constitution.schemas import (
    EventEnvelope,
    Evidence,
    EpistemicStatus,
    Intent,
    CapabilityManifest,
    CapabilityLifecycle,
)
from kernel.events.ledger import EventLedger
from kernel.registry.capability_registry import CapabilityRegistry


def test_event_ledger_hash_chain(tmp_path):
    ledger = EventLedger(tmp_path / "events.db")
    e1 = ledger.append(EventEnvelope(event_type="test.1", producer_id="test"))
    e2 = ledger.append(EventEnvelope(event_type="test.2", producer_id="test"))
    assert ledger.verify_chain()
    assert e2.previous_event_hash == e1.payload_hash


def test_capability_cannot_activate_without_approval():
    reg = CapabilityRegistry(db_path=":memory:")
    cap = CapabilityManifest(name="test-cap", description="demo")
    reg.register(cap)
    try:
        reg.transition(cap.capability_id, CapabilityLifecycle.ACTIVE, authorized_by="x")
        assert False, "should have raised"
    except PermissionError as e:
        assert "CCOS-004" in str(e)


def test_evidence_starts_unverified():
    ev = Evidence(claim="sky is blue", source="observation")
    assert ev.epistemic_status == EpistemicStatus.UNVERIFIED
