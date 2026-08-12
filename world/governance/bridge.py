"""World actions require capability approval (CCOS-style)."""

from __future__ import annotations

from typing import Any, Dict, Optional, Set

from world.core.world import World
from world.laboratory.fork import Laboratory, ExperimentResult

KNOWN_WORLD_CAPS = {
    "world.observe",
    "world.tick",
    "world.spawn",
    "world.experiment",
    "world.fork",
}

FORBIDDEN = {"world.mutate_live_unchecked", "world.delete_all"}


class WorldCapabilityBridge:
    def __init__(self, world: World, ccos: Any = None):
        self.world = world
        self.ccos = ccos
        self.grants: Dict[str, Set[str]] = {}
        self.lab = Laboratory(world)
        self.denials = 0
        self.approvals = 0

    def grant(self, agent_id: str, *caps: str) -> None:
        self.grants.setdefault(agent_id, set()).update(caps)

    def _allowed(self, agent_id: str, capability: str) -> bool:
        if capability in FORBIDDEN:
            self.denials += 1
            return False
        if capability not in KNOWN_WORLD_CAPS:
            self.denials += 1
            return False
        if self.ccos is not None:
            try:
                d = self.ccos.request_capability(agent_id, capability, purpose="world")
                ok = d.approved
                if not ok:
                    self.denials += 1
                else:
                    self.approvals += 1
                return ok
            except Exception:
                pass
        ok = capability in self.grants.get(agent_id, set())
        if ok:
            self.approvals += 1
        else:
            self.denials += 1
        return ok

    def observe(self, agent_id: str, noise: float = 0.05) -> Optional[Dict[str, Any]]:
        if not self._allowed(agent_id, "world.observe"):
            return None
        from world.observation.sensors import observe_world
        obs = observe_world(self.world, observer_id=agent_id, noise=noise)
        return {
            "tick": obs.tick,
            "entities": obs.entities,
            "resources": obs.resources,
            "noise": obs.noise_level,
            "complete": obs.complete,
        }

    def request_experiment(
        self, agent_id: str, ticks: int = 5, interventions: Optional[list] = None
    ) -> Optional[ExperimentResult]:
        if not self._allowed(agent_id, "world.experiment"):
            return None
        if not self._allowed(agent_id, "world.fork"):
            return None
        return self.lab.run_experiment(ticks=ticks, interventions=interventions)
