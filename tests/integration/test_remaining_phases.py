"""Tests for remaining production phases: reasoning, replication, invariants, civilization, physics."""

from pathlib import Path
from uuid import uuid4

from constitution.schemas.event import EventEnvelope, EpistemicStatus
from cognition.reasoning.backend import DeterministicReasoner
from kernel.events.replication import ReplicationCluster
from constitution.invariants import InvariantMonitor
from agents.civilization.runtime import CivilizationRuntime
from simulation.physics import PhysicsCosmos
from hermes.shell import Hermes


def test_reasoning_never_verified(tmp_path):
    h = Hermes(tmp_path)
    r = DeterministicReasoner(h.ledger).reason("plan something", {"evidence_ids": ["e"]})
    assert r.epistemic_status == EpistemicStatus.UNVERIFIED
    assert r.confidence < 0.5


def test_replication_sync(tmp_path):
    cluster = ReplicationCluster()
    a = cluster.add_node("a", tmp_path / "a")
    b = cluster.add_node("b", tmp_path / "b")
    a.append_local(EventEnvelope(event_type="x", producer_id="a", payload={"n": 1}))
    result = cluster.sync(a.node_id, b.node_id)
    assert result["imported"] == 1
    assert result["target_chain_valid"] is True
    assert b.ledger.count() == 1


def test_invariants_pass(tmp_path):
    h = Hermes(tmp_path)
    mon = InvariantMonitor(h.ledger)
    results = mon.run_all()
    assert all(r.passed for r in results)


def test_civilization_task_flow(tmp_path):
    h = Hermes(tmp_path)
    civ = CivilizationRuntime(h.population, h.organizations, h.ledger)
    civ.bootstrap_civilization(f"Civ-{uuid4().hex[:6]}")
    t = civ.submit_task("test", "researcher")
    assigned = civ.assign_tasks()
    assert assigned
    civ.complete_task(assigned[0].task_id, {"ok": True})
    assert civ.status()["completed"] == 1


def test_physics_tick(tmp_path):
    h = Hermes(tmp_path)
    p = PhysicsCosmos(h.ledger, seed=1)
    p.spawn(mass=1.0, x=10, y=10)
    p.spawn(mass=2.0, x=90, y=90)
    m = p.tick(5)
    assert m["tick"] == 5.0
    assert m["n_bodies"] == 2.0
