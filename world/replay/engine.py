"""Replay engine — determinism verification."""
from __future__ import annotations
from typing import Any, Dict, List
from world.core.world import World
from world.state.snapshot import take_snapshot, restore_snapshot

class ReplayEngine:
    def __init__(self):
        self.recordings: List[Dict[str, Any]] = []

    def record_run(self, world: World, ticks: int, dt: float = 1.0) -> Dict[str, Any]:
        start = take_snapshot(world)
        hashes = [world.hash()]
        for _ in range(ticks):
            hashes.append(world.tick(dt))
        rec = {"start": start, "hashes": hashes, "ticks": ticks, "dt": dt, "final_hash": hashes[-1]}
        self.recordings.append(rec)
        return rec

    def verify(self, world_factory, recording: Dict[str, Any]) -> bool:
        """Rebuild from snapshot and confirm hash chain."""
        w = world_factory()
        restore_snapshot(w, recording["start"])
        if w.hash() != recording["hashes"][0]:
            return False
        for i in range(recording["ticks"]):
            h = w.tick(recording["dt"])
            if h != recording["hashes"][i + 1]:
                return False
        return True
