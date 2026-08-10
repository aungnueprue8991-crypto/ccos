"""Production tests for COS core."""

from pathlib import Path
import tempfile

from constitution.schemas.event import EventEnvelope
from constitution.schemas.capability import CapabilityManifest, CapabilityLifecycle
from kernel.events.ledger import EventLedger
from kernel.registry.capability_registry import CapabilityRegistry
from kernel.resources.manager import ResourceManager
from kernel.ipc.channels import IPC
from kernel.scheduler.scheduler import Scheduler
import time


def test_ledger_persistence_and_chain(tmp_path):
    db = tmp_path / "e.db"
    ledger = EventLedger(db)
    ledger.append(EventEnvelope(event_type="t1", producer_id="p"))
    ledger.append(EventEnvelope(event_type="t2", producer_id="p"))
    assert ledger.verify_chain()
    assert ledger.count() == 2
    ledger2 = EventLedger(db)
    assert ledger2.count() == 2
    assert ledger2.verify_chain()


def test_capability_guard(tmp_path):
    reg = CapabilityRegistry(db_path=tmp_path / "c.db")
    m = CapabilityManifest(name="x", description="d")
    reg.register(m)
    try:
        reg.transition(m.capability_id, CapabilityLifecycle.ACTIVE, authorized_by="x")
        assert False
    except PermissionError as e:
        assert "CCOS-004" in str(e)


def test_resources():
    rm = ResourceManager()
    assert rm.allocate("a", cpu=10)
    assert not rm.allocate("a", cpu=1000)


def test_ipc():
    ipc = IPC()
    ipc.send("ch", "s", {"v": 1})
    msg = ipc.receive("ch")
    assert msg is not None
    assert msg.payload["v"] == 1


def test_scheduler():
    s = Scheduler(max_concurrent=2)
    s.start()
    tid = s.submit("job", lambda: 42, priority=1)
    time.sleep(0.3)
    t = s.get(tid)
    assert t is not None
    assert t.state.value in ("COMPLETED", "RUNNING", "PENDING")
    s.stop()
