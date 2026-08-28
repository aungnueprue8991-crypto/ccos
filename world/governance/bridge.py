"""World actions require capability approval (CCOS-style).

Strict mode (CCOS_STRICT=1 or strict=True):
  - Local grants are ignored.
  - Only an explicit CCOS client decision can approve.
  - Missing/failing CCOS client → DENY.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
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


def _env_strict() -> bool:
    v = os.environ.get("CCOS_STRICT", "").strip().lower()
    return v in ("1", "true", "yes", "on")


@dataclass
class CapabilityDecision:
    approved: bool
    reason: str = ""
    capability: str = ""
    agent_id: str = ""


class StrictCCOSClient:
    """Minimal CCOS client: approve only known world caps on an allow-list."""

    def __init__(self):
        self._allow: Dict[str, Set[str]] = {}
        self.decisions: list = []

    def allow(self, agent_id: str, *caps: str) -> None:
        self._allow.setdefault(agent_id, set()).update(caps)

    def revoke(self, agent_id: str, *caps: str) -> None:
        s = self._allow.get(agent_id, set())
        for c in caps:
            s.discard(c)

    def request_capability(
        self, agent_id: str, capability: str, purpose: str = ""
    ) -> CapabilityDecision:
        ok = capability in self._allow.get(agent_id, set())
        d = CapabilityDecision(
            approved=ok,
            reason="strict_allowlist" if ok else "strict_deny",
            capability=capability,
            agent_id=agent_id,
        )
        self.decisions.append(d)
        return d


class WorldCapabilityBridge:
    """Gate world mutations; integrate with CivilizationCCOS when available."""

    def __init__(
        self,
        world: World,
        ccos: Any = None,
        strict: Optional[bool] = None,
    ):
        self.world = world
        self.ccos = ccos
        self.strict = _env_strict() if strict is None else bool(strict)
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
                ok = bool(getattr(d, "approved", d))
                if ok:
                    self.approvals += 1
                else:
                    self.denials += 1
                return ok
            except Exception:
                if self.strict:
                    self.denials += 1
                    return False

        if self.strict:
            self.denials += 1
            return False

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
        self,
        agent_id: str,
        ticks: int = 5,
        interventions: Optional[list] = None,
    ) -> Optional[ExperimentResult]:
        if not self._allowed(agent_id, "world.experiment"):
            return None
        if not self._allowed(agent_id, "world.fork"):
            return None
        return self.lab.run_experiment(ticks=ticks, interventions=interventions)
