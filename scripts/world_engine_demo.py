#!/usr/bin/env python3
"""World Engine Phase-1 demo — determinism, fork experiment, observation."""

from world.core.world import World
from world.core.entity import Transform, Velocity, Mass, Energy, Label
from world.laboratory.fork import Laboratory
from world.observation.sensors import observe_world
from world.governance.bridge import WorldCapabilityBridge

def main():
    w = World(seed=7, name="demo")
    w.spawn(Label("probe", "agent"), Transform(0, 5, 0), Velocity(0.5, 0, 0), Mass(1), Energy(100))
    w.spawn(Label("target", "object"), Transform(10, 0, 0), Velocity(0, 0, 0), Mass(3), Energy(40))

    print("World Engine Phase-1")
    print("===================")
    for i in range(5):
        h = w.tick()
        print(f"  tick={w.tick_count} hash={h[:16]}…")

    w2 = World(seed=7)
    w2.spawn(Label("probe", "agent"), Transform(0, 5, 0), Velocity(0.5, 0, 0), Mass(1), Energy(100))
    w2.spawn(Label("target", "object"), Transform(10, 0, 0), Velocity(0, 0, 0), Mass(3), Energy(40))
    for _ in range(5):
        w2.tick()
    assert w.hash() == w2.hash(), "determinism broken"
    print("Determinism: PASS")

    lab = Laboratory(w)
    before = w.hash()
    exp = lab.run_experiment(ticks=8, interventions=[{"entity_id": 1, "vx": 2.0}])
    print(f"Fork experiment: live_unchanged={w.hash()==before} result_hash={exp.result_hash[:16]}…")

    bridge = WorldCapabilityBridge(w)
    bridge.grant("scientist-1", "world.observe", "world.experiment", "world.fork")
    obs = bridge.observe("scientist-1", noise=0.02)
    print(f"Observation entities={len(obs['entities'])} complete={obs['complete']}")
    print("World Engine demo OK")

if __name__ == "__main__":
    main()
