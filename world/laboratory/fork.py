"""Laboratory — world forks for experiments (not live civilization)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from world.core.world import World
from world.core.entity import Transform, Velocity, Energy
from world.state.snapshot import take_snapshot, restore_snapshot
from ags.shared.types import new_id, now_ts


@dataclass
class ExperimentResult:
    experiment_id: str
    fork_id: str
    parent_hash: str
    result_hash: str
    ticks: int
    measurements: Dict[str, Any]
    success: bool
    notes: str = ""


class WorldFork:
    """Isolated snapshot clone for experiments."""

    def __init__(self, parent: World, fork_id: Optional[str] = None):
        self.fork_id = fork_id or new_id()
        self.parent_hash = parent.hash()
        snap = take_snapshot(parent)
        self.world = World(seed=parent.seed, name=f"fork-{self.fork_id[:8]}")
        restore_snapshot(self.world, snap)
        self.created_at = now_ts()

    def run(self, ticks: int = 10, dt: float = 1.0) -> str:
        h = self.parent_hash
        for _ in range(ticks):
            h = self.world.tick(dt)
        return h

    def measure(self) -> Dict[str, Any]:
        positions = []
        for e in self.world.query(Transform):
            t = e.get(Transform)
            positions.append({"id": e.id, "x": t.x, "y": t.y, "z": t.z})
        energies = []
        for e in self.world.query(Energy):
            energies.append({"id": e.id, "energy": e.get(Energy).value})
        return {
            "tick": self.world.tick_count,
            "hash": self.world.hash(),
            "positions": positions,
            "energies": energies,
            "entity_count": len([e for e in self.world.entities.values() if e.active]),
        }


class Laboratory:
    def __init__(self, live_world: World):
        self.live = live_world
        self.forks: Dict[str, WorldFork] = {}
        self.results: List[ExperimentResult] = []

    def create_fork(self) -> WorldFork:
        f = WorldFork(self.live)
        self.forks[f.fork_id] = f
        return f

    def run_experiment(
        self,
        ticks: int = 5,
        interventions: Optional[List[Dict[str, Any]]] = None,
    ) -> ExperimentResult:
        fork = self.create_fork()
        parent_hash = fork.parent_hash
        for iv in interventions or []:
            eid = iv.get("entity_id")
            e = fork.world.get(eid)
            if not e:
                continue
            if "vx" in iv and e.get(Velocity):
                e.get(Velocity).vx = float(iv["vx"])
            if "energy" in iv and e.get(Energy):
                e.get(Energy).value = float(iv["energy"])
        result_hash = fork.run(ticks=ticks)
        measurements = fork.measure()
        exp = ExperimentResult(
            experiment_id=new_id(),
            fork_id=fork.fork_id,
            parent_hash=parent_hash,
            result_hash=result_hash,
            ticks=ticks,
            measurements=measurements,
            success=True,
        )
        self.results.append(exp)
        return exp
