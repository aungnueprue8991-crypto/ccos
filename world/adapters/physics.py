"""Simple physics adapter — not a full engine."""

from __future__ import annotations

from world.core.entity import Velocity
from world.core.world import World


def apply_impulse(world: World, entity_id: int, dvx: float = 0.0, dvy: float = 0.0, dvz: float = 0.0) -> bool:
    e = world.get(entity_id)
    if not e:
        return False
    v = e.get(Velocity)
    if not v:
        return False
    v.vx = round(v.vx + dvx, 6)
    v.vy = round(v.vy + dvy, 6)
    v.vz = round(v.vz + dvz, 6)
    return True
