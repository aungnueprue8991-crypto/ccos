"""Strict-mode capability bridge + external oracle tests."""

from __future__ import annotations

from world.core.world import World
from world.core.entity import Label, Transform, Energy
from world.governance.bridge import WorldCapabilityBridge, StrictCCOSClient
from world.science.oracle import ThermoEquilibriumOracle, MassConservationOracle
from world.science.loop import ScientificCivilizationLoop


def test_strict_denies_local_grants():
    w = World(seed=1)
    w.spawn(Label("x"), Transform(), Energy(1))
    bridge = WorldCapabilityBridge(w, strict=True)
    bridge.grant("agent-1", "world.observe", "world.experiment", "world.fork")
    assert bridge.observe("agent-1") is None
    assert bridge.denials >= 1


def test_strict_allows_via_client():
    w = World(seed=1)
    w.spawn(Label("x"), Transform(), Energy(1))
    client = StrictCCOSClient()
    client.allow("agent-1", "world.observe")
    bridge = WorldCapabilityBridge(w, ccos=client, strict=True)
    obs = bridge.observe("agent-1")
    assert obs is not None
    assert bridge.approvals >= 1
    assert bridge.request_experiment("agent-1", ticks=1) is None


def test_non_strict_local_grants_work():
    w = World(seed=1)
    w.spawn(Label("x"), Transform(), Energy(1))
    bridge = WorldCapabilityBridge(w, strict=False)
    bridge.grant("agent-1", "world.observe")
    assert bridge.observe("agent-1") is not None


def test_thermo_oracle_accepts_equilibrium():
    oracle = ThermoEquilibriumOracle(tol_k=1.0)
    v = oracle.verify({
        "bodies": [
            {"name": "hot", "mass_kg": 1.0, "temp_k": 373.15, "c_j_per_kg_k": 4180.0},
            {"name": "cold", "mass_kg": 1.0, "temp_k": 273.15, "c_j_per_kg_k": 4180.0},
        ],
        "final_temps": {"hot": 323.15, "cold": 323.15},
    })
    assert v.accepted
    assert v.independent
    assert abs(v.details["t_eq"] - 323.15) < 0.01


def test_thermo_oracle_rejects_far_from_eq():
    oracle = ThermoEquilibriumOracle(tol_k=1.0)
    v = oracle.verify({
        "bodies": [
            {"name": "hot", "mass_kg": 1.0, "temp_k": 373.15, "c_j_per_kg_k": 4180.0},
            {"name": "cold", "mass_kg": 1.0, "temp_k": 273.15, "c_j_per_kg_k": 4180.0},
        ],
        "final_temps": {"hot": 370.0, "cold": 276.0},
    })
    assert not v.accepted


def test_mass_oracle():
    o = MassConservationOracle()
    assert o.verify({"initial_mass": 10.0, "final_mass": 10.0}).accepted
    assert not o.verify({"initial_mass": 10.0, "final_mass": 9.0}).accepted


def test_science_loop_uses_oracle():
    r = ScientificCivilizationLoop(seed=42).run_thermodynamics_experiment()
    assert r.success
    assert r.discovery == "thermal_equilibration_confirmed"
    assert any(e.get("type") == "oracle_verdict" for e in r.ledger_events)
    assert any(e.get("accepted") for e in r.ledger_events if e.get("type") == "oracle_verdict")
