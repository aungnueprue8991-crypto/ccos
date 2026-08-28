"""World Engine Phase-1 — determinism, forks, observation, governance."""

from world.core.world import World
from world.core.entity import Transform, Velocity, Mass, Energy, Label
from world.state.hashing import canonical_state
from world.state.snapshot import take_snapshot, restore_snapshot
from world.laboratory.fork import Laboratory
from world.observation.sensors import observe_world
from world.governance.bridge import WorldCapabilityBridge
from world.adapters.physics import apply_impulse
from world.resources.economy import ResourceLedger


def _seeded_world(seed=7):
    w = World(seed=seed)
    w.spawn(Label("ball", "object"), Transform(0, 10, 0), Velocity(1, 0, 0), Mass(1.0), Energy(50))
    w.spawn(Label("rock", "object"), Transform(5, 0, 0), Velocity(0, 0, 0), Mass(2.0), Energy(20))
    return w


def test_determinism_same_seed_same_hash():
    w1 = _seeded_world(42)
    w2 = _seeded_world(42)
    for _ in range(5):
        h1 = w1.tick()
        h2 = w2.tick()
    assert h1 == h2
    assert w1.hash() == w2.hash()


def test_different_seed_diverges():
    w1 = _seeded_world(1)
    w2 = _seeded_world(2)
    for _ in range(3):
        w1.tick()
        w2.tick()
    assert canonical_state(w1)["seed"] != canonical_state(w2)["seed"]
    assert w1.hash() != w2.hash()


def test_snapshot_restore_preserves_hash():
    w = _seeded_world(3)
    for _ in range(4):
        w.tick()
    h = w.hash()
    snap = take_snapshot(w)
    w2 = World(seed=0)
    restore_snapshot(w2, snap)
    assert w2.hash() == h
    w2.tick()
    w.tick()
    assert w2.hash() == w.hash()


def test_lab_fork_does_not_mutate_live():
    live = _seeded_world(9)
    live.tick()
    live_hash = live.hash()
    lab = Laboratory(live)
    exp = lab.run_experiment(ticks=5, interventions=[{"entity_id": 1, "vx": 99.0}])
    assert exp.success
    assert live.hash() == live_hash
    assert exp.result_hash != live_hash or exp.ticks > 0


def test_observation_not_complete_ground_truth():
    w = _seeded_world(5)
    w.tick()
    obs = observe_world(w, observer_id="agent", noise=0.1, max_range=12.0, origin=(0, 0, 0))
    assert obs.complete is False
    assert obs.noise_level == 0.1
    ids = [e["id"] for e in obs.entities]
    assert 1 in ids
    obs_near = observe_world(w, observer_id="agent", noise=0.0, max_range=2.0, origin=(0, 0, 0))
    assert len(obs_near.entities) <= len(obs.entities)


def test_capability_bridge_denies_without_grant():
    w = _seeded_world(1)
    bridge = WorldCapabilityBridge(w)
    assert bridge.observe("agent-x") is None
    bridge.grant("agent-x", "world.observe")
    obs = bridge.observe("agent-x")
    assert obs is not None
    assert "entities" in obs


def test_experiment_requires_capability():
    w = _seeded_world(1)
    bridge = WorldCapabilityBridge(w)
    assert bridge.request_experiment("a") is None
    bridge.grant("a", "world.experiment", "world.fork")
    exp = bridge.request_experiment("a", ticks=3)
    assert exp is not None and exp.success


def test_impulse_adapter():
    w = _seeded_world(1)
    e = w.get(1)
    assert apply_impulse(w, 1, dvx=2.0)
    assert e.get(Velocity).vx == 3.0


def test_resource_ledger():
    r = ResourceLedger()
    assert r.spend("energy", 100)
    assert not r.spend("energy", 99999)


def test_query_ordered():
    w = _seeded_world(1)
    ids = [e.id for e in w.query(Transform)]
    assert ids == sorted(ids)
