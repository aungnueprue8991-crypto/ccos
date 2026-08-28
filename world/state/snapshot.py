"""World snapshots for forks and replay."""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from world.core.entity import (
    Entity, Transform, Velocity, Mass, Energy, Label, ResourceStock,
)

if TYPE_CHECKING:
    from world.core.world import World

_COMPONENT_TYPES = {
    "Transform": Transform,
    "Velocity": Velocity,
    "Mass": Mass,
    "Energy": Energy,
    "Label": Label,
    "ResourceStock": ResourceStock,
}


def take_snapshot(world: "World") -> Dict[str, Any]:
    from world.state.hashing import canonical_state, state_hash
    state = canonical_state(world)
    return {
        "state": state,
        "hash": state_hash(state),
        "next_id": world._next_id,
        "event_log": list(world.event_log[-100:]),
    }


def restore_snapshot(world: "World", snap: Dict[str, Any]) -> None:
    state = snap["state"]
    world.seed = state["seed"]
    world.tick_count = state["tick"]
    world.resources = dict(state["resources"])
    world._next_id = snap.get("next_id", world._next_id)
    world.entities.clear()
    for ed in state["entities"]:
        e = Entity(ed["id"])
        e.active = ed["active"]
        for cname, cdata in ed["components"].items():
            cls = _COMPONENT_TYPES.get(cname)
            if cls:
                e.add(cls(**cdata))
        world.entities[e.id] = e
    world.event_log = list(snap.get("event_log", []))
