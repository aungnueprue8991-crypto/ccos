"""Physics adapter — Newtonian impulses, drag, and simple gravity on ECS entities."""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

from world.core.entity import Velocity, Mass, Transform
from world.core.world import World


def _q(x: float, nd: int = 6) -> float:
    return round(float(x), nd)


def apply_impulse(
    world: World,
    entity_id: int,
    dvx: float = 0.0,
    dvy: float = 0.0,
    dvz: float = 0.0,
) -> bool:
    e = world.get(entity_id)
    if not e:
        return False
    v = e.get(Velocity)
    if not v:
        return False
    v.vx = _q(v.vx + dvx)
    v.vy = _q(v.vy + dvy)
    v.vz = _q(v.vz + dvz)
    return True


def apply_force(
    world: World,
    entity_id: int,
    fx: float,
    fy: float = 0.0,
    fz: float = 0.0,
    dt: float = 1.0,
) -> bool:
    e = world.get(entity_id)
    if not e:
        return False
    v = e.get(Velocity)
    m = e.get(Mass)
    if not v or not m or m.value <= 0:
        return False
    inv = 1.0 / m.value
    return apply_impulse(world, entity_id, fx * inv * dt, fy * inv * dt, fz * inv * dt)


class PhysicsAdapter:
    def __init__(self, world: World, gravity: Tuple[float, float, float] = (0.0, -9.81, 0.0)):
        self.world = world
        self.gravity = gravity
        self.drag_coeff = 0.0

    def set_gravity(self, gx: float = 0.0, gy: float = -9.81, gz: float = 0.0) -> None:
        self.gravity = (gx, gy, gz)

    def integrate(self, dt: float = 0.1) -> Dict[str, int]:
        moved = 0
        gx, gy, gz = self.gravity
        for eid, ent in self.world.entities.items():
            v = ent.get(Velocity)
            t = ent.get(Transform)
            if not v or not t:
                continue
            v.vx = _q(v.vx + gx * dt)
            v.vy = _q(v.vy + gy * dt)
            v.vz = _q(v.vz + gz * dt)
            if self.drag_coeff > 0:
                damp = max(0.0, 1.0 - self.drag_coeff * dt)
                v.vx = _q(v.vx * damp)
                v.vy = _q(v.vy * damp)
                v.vz = _q(v.vz * damp)
            t.x = _q(t.x + v.vx * dt)
            t.y = _q(t.y + v.vy * dt)
            t.z = _q(t.z + v.vz * dt)
            moved += 1
        return {"moved": moved, "dt": dt}

    def kinetic_energy(self, entity_id: int) -> Optional[float]:
        e = self.world.get(entity_id)
        if not e:
            return None
        v = e.get(Velocity)
        m = e.get(Mass)
        if not v or not m:
            return None
        speed2 = v.vx * v.vx + v.vy * v.vy + v.vz * v.vz
        return _q(0.5 * m.value * speed2)

    def collide_elastic(self, a_id: int, b_id: int, restitution: float = 1.0) -> bool:
        ea, eb = self.world.get(a_id), self.world.get(b_id)
        if not ea or not eb:
            return False
        va, vb = ea.get(Velocity), eb.get(Velocity)
        ma, mb = ea.get(Mass), eb.get(Mass)
        if not all([va, vb, ma, mb]) or ma.value <= 0 or mb.value <= 0:
            return False
        u1, u2 = va.vx, vb.vx
        m1, m2 = ma.value, mb.value
        e = max(0.0, min(1.0, restitution))
        v1 = (u1 * (m1 - e * m2) + u2 * m2 * (1 + e)) / (m1 + m2)
        v2 = (u2 * (m2 - e * m1) + u1 * m1 * (1 + e)) / (m1 + m2)
        va.vx = _q(v1)
        vb.vx = _q(v2)
        return True

    def distance(self, a_id: int, b_id: int) -> Optional[float]:
        ea, eb = self.world.get(a_id), self.world.get(b_id)
        if not ea or not eb:
            return None
        ta, tb = ea.get(Transform), eb.get(Transform)
        if not ta or not tb:
            return None
        return _q(math.sqrt((ta.x - tb.x) ** 2 + (ta.y - tb.y) ** 2 + (ta.z - tb.z) ** 2))
