"""Canonical state serialization + SHA-256 hashing for determinism tests."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from world.core.world import World


def _component_dict(c: Any) -> Dict[str, Any]:
    if hasattr(c, "__dict__"):
        return {k: v for k, v in vars(c).items() if not k.startswith("_")}
    return {}


def canonical_state(world: "World") -> Dict[str, Any]:
    entities = []
    for eid in sorted(world.entities.keys()):
        e = world.entities[eid]
        comps = {}
        for cls, comp in sorted(e.components.items(), key=lambda x: x[0].__name__):
            comps[cls.__name__] = _component_dict(comp)
        entities.append({
            "id": eid,
            "active": e.active,
            "components": comps,
        })
    return {
        "engine_version": world.engine_version,
        "seed": world.seed,
        "tick": world.tick_count,
        "resources": {k: world.resources[k] for k in sorted(world.resources.keys())},
        "entities": entities,
    }


def state_hash(state: Dict[str, Any]) -> str:
    blob = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
