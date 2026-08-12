"""Deterministic World — ECS container + tick pipeline."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Type

from world.core.entity import Entity, Component, Transform, Velocity, Mass, Energy, Label, ResourceStock
from world.core.systems import DEFAULT_SYSTEMS
from world.state.hashing import canonical_state, state_hash


class World:
    def __init__(self, seed: int = 0, name: str = "world"):
        self.name = name
        self.seed = seed
        self.tick_count = 0
        self._next_id = 1
        self.entities: Dict[int, Entity] = {}
        self.resources: Dict[str, Any] = {
            "gravity": 9.81,
            "energy_pool": 1000.0,
            "time": 0.0,
        }
        self.systems: List[Callable] = list(DEFAULT_SYSTEMS)
        self.event_log: List[Dict[str, Any]] = []
        self.engine_version = "0.1.0-phase1"

    def spawn(self, *components: Component) -> Entity:
        eid = self._next_id
        self._next_id += 1
        e = Entity(eid)
        for c in components:
            e.add(c)
        self.entities[eid] = e
        self.event_log.append({"type": "spawn", "id": eid, "tick": self.tick_count})
        return e

    def despawn(self, entity_id: int) -> bool:
        e = self.entities.get(entity_id)
        if not e:
            return False
        e.active = False
        self.event_log.append({"type": "despawn", "id": entity_id, "tick": self.tick_count})
        return True

    def get(self, entity_id: int) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def query(self, *component_types: Type) -> List[Entity]:
        out = []
        for eid in sorted(self.entities.keys()):
            e = self.entities[eid]
            if not e.active:
                continue
            if all(e.has(ct) for ct in component_types):
                out.append(e)
        return out

    def tick(self, dt: float = 1.0) -> str:
        """Advance world; return canonical state hash."""
        self.tick_count += 1
        self.resources["time"] = round(self.resources["time"] + dt, 6)
        for system in self.systems:
            system(self, dt)
        self.event_log.append({"type": "tick", "n": self.tick_count, "dt": dt})
        return self.hash()

    def hash(self) -> str:
        return state_hash(canonical_state(self))

    def snapshot(self) -> Dict[str, Any]:
        from world.state.snapshot import take_snapshot
        return take_snapshot(self)

    def restore(self, snap: Dict[str, Any]) -> None:
        from world.state.snapshot import restore_snapshot
        restore_snapshot(self, snap)
