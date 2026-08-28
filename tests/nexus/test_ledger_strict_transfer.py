"""EventLedger wiring, strict world path, hidden-domain transfer."""

from __future__ import annotations

from pathlib import Path
import tempfile

from nexus.orchestration.cognitive_loop import CognitiveOrchestrator
from nexus.transfer.hidden_domain import HiddenDomainBenchmark
from world.governance.bridge import StrictCCOSClient, WorldCapabilityBridge
from world.core.world import World
from world.core.entity import Label, Transform, Energy
from world.science.loop import ScientificCivilizationLoop


def test_nexus_events_on_event_ledger():
    path = Path(tempfile.mkdtemp()) / "n.db"
    orch = CognitiveOrchestrator(seed=42, ledger_path=path, strict_world=True)
    r = orch.run_cycle(run_world_experiment=True, run_hidden_transfer=True)
    assert r.event_ledger_count >= 8
    assert r.event_ledger_chain_ok is True
    assert any(e.get("type") == "cognitive_heart" for e in r.ledger_events)
    assert any(e.get("type") == "hidden_domain_transfer" for e in r.ledger_events)
    assert orch.event_bridge.ledger.find_by_type("nexus.cognitive_heart")
    assert orch.event_bridge.verify_chain()


def test_strict_world_loop_requires_client():
    loop = ScientificCivilizationLoop(seed=1, strict=True, ccos=StrictCCOSClient())
    r = loop.run_thermodynamics_experiment("sci")
    assert r.success is True
    assert r.discovery == "thermal_equilibration_confirmed"


def test_strict_bridge_blocks_without_client_allow():
    w = World(seed=1)
    w.spawn(Label("x"), Transform(), Energy(1))
    b = WorldCapabilityBridge(w, strict=True)
    b.grant("a", "world.observe")
    assert b.observe("a") is None


def test_hidden_domain_transfer_hit():
    bench = HiddenDomainBenchmark()
    r = bench.run(mechanism="thermal_equilibration_confirmed", pool_a=100, pool_b=20)
    assert r.similarity >= 0.5
    assert r.transfer_hit is True
    assert abs(r.hidden_prediction["pool_a"] - r.hidden_actual["pool_a"]) < 3.0


def test_orchestrator_strict_and_hidden():
    path = Path(tempfile.mkdtemp()) / "n2.db"
    orch = CognitiveOrchestrator(seed=7, ledger_path=path, strict_world=True)
    r = orch.run_cycle()
    assert r.strict_world is True
    assert r.oracle_accepted is True
    assert r.hidden_transfer is not None
    assert r.hidden_transfer["transfer_hit"] is True
    assert r.event_ledger_chain_ok is True
