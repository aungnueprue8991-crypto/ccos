"""Observation ≠ ground truth — noise, occlusion, limited range."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from world.core.entity import Transform, Energy, Label

if TYPE_CHECKING:
    from world.core.world import World


@dataclass
class Observation:
    tick: int
    observer_id: str
    entities: List[Dict[str, Any]] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    noise_level: float = 0.0
    complete: bool = False


def observe_entity(
    world: "World",
    entity_id: int,
    noise: float = 0.0,
    rng: Optional[random.Random] = None,
) -> Optional[Dict[str, Any]]:
    e = world.get(entity_id)
    if not e or not e.active:
        return None
    rng = rng or random.Random(world.seed + entity_id + world.tick_count)
    t = e.get(Transform)
    lab = e.get(Label)
    en = e.get(Energy)
    data: Dict[str, Any] = {"id": entity_id}
    if lab:
        data["name"] = lab.name
        data["kind"] = lab.kind
    if t:
        data["x"] = round(t.x + (rng.uniform(-noise, noise) if noise else 0), 4)
        data["y"] = round(t.y + (rng.uniform(-noise, noise) if noise else 0), 4)
        data["z"] = round(t.z + (rng.uniform(-noise, noise) if noise else 0), 4)
    if en:
        data["energy"] = round(en.value + (rng.uniform(-noise * 5, noise * 5) if noise else 0), 4)
    return data


def observe_world(
    world: "World",
    observer_id: str = "sensor",
    noise: float = 0.05,
    max_range: Optional[float] = None,
    origin: Optional[tuple] = None,
) -> Observation:
    rng = random.Random(world.seed + world.tick_count + hash(observer_id) % 10000)
    origin = origin or (0.0, 0.0, 0.0)
    entities = []
    for e in world.query(Transform):
        t = e.get(Transform)
        if max_range is not None:
            dist = math.sqrt(
                (t.x - origin[0]) ** 2 + (t.y - origin[1]) ** 2 + (t.z - origin[2]) ** 2
            )
            if dist > max_range:
                continue
        obs = observe_entity(world, e.id, noise=noise, rng=rng)
        if obs:
            entities.append(obs)
    return Observation(
        tick=world.tick_count,
        observer_id=observer_id,
        entities=entities,
        resources={"time": world.resources.get("time")},
        noise_level=noise,
        complete=False,
    )
