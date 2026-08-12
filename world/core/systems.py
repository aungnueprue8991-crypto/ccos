"""Deterministic system pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from world.core.entity import Transform, Velocity, Mass, Energy

if TYPE_CHECKING:
    from world.core.world import World


def movement_system(world: "World", dt: float) -> None:
    """Integrate velocity into position — fixed order by entity id."""
    for eid in sorted(world.entities.keys()):
        e = world.entities[eid]
        if not e.active:
            continue
        t = e.get(Transform)
        v = e.get(Velocity)
        if t is None or v is None:
            continue
        t.x = round(t.x + v.vx * dt, 6)
        t.y = round(t.y + v.vy * dt, 6)
        t.z = round(t.z + v.vz * dt, 6)


def energy_decay_system(world: "World", dt: float) -> None:
    for eid in sorted(world.entities.keys()):
        e = world.entities[eid]
        en = e.get(Energy)
        if en is None:
            continue
        en.value = round(max(0.0, en.value - 0.01 * dt), 6)


def gravity_system(world: "World", dt: float) -> None:
    """Simple downward acceleration if mass present."""
    g = world.resources.get("gravity", 9.81)
    for eid in sorted(world.entities.keys()):
        e = world.entities[eid]
        v = e.get(Velocity)
        m = e.get(Mass)
        if v is None or m is None:
            continue
        v.vy = round(v.vy - g * dt * 0.01, 6)


DEFAULT_SYSTEMS = [movement_system, gravity_system, energy_decay_system]
