"""LivingAgent — drive-based organism discovering XOR-lamp rule."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ags.living.genome import mutate
from ags.living.world import XORLampWorld


@dataclass
class LivingState:
    lifecycle: str = "INFANT"
    experience: int = 0
    discoveries: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0
    offspring_count: int = 0
    curiosity_pressure: float = 0.0
    reproduction_pressure: float = 0.0
    known_rule: Optional[str] = None
    causal_rules: List[str] = field(default_factory=list)


class LivingAgent:
    def __init__(
        self,
        agent_id: str,
        genome: Dict[str, Any],
        world: XORLampWorld,
        ccos: Any = None,
    ):
        self.id = agent_id
        self.genome = genome
        self.world = world
        self.ccos = ccos
        self.state = LivingState()
        self.episodic: List[Dict[str, Any]] = []
        self._last_obs: Dict[str, Any] = {}
        self._thresholds = genome.get("fixed_parameters", {}).get("stage_thresholds") or {
            "INFANT_to_CHILD": 3,
            "CHILD_to_ADOLESCENT": 6,
            "ADOLESCENT_to_MATURE": 10,
        }

    def run_cycle(self) -> Dict[str, Any]:
        obs = self.world.observe()
        self._last_obs = obs
        self.state.experience += 1
        self._update_lifecycle()
        self._update_curiosity(obs)
        self._update_reproduction()

        action = self._choose_action(obs)
        result = self.world.perform_action(action)
        new_obs = result.get("observation") or self.world.observe()
        self._learn(obs, action, new_obs)

        events: List[str] = []
        if self.state.reproduction_pressure > 0.6 and self.state.lifecycle in ("ADOLESCENT", "MATURE"):
            events.append("reproduction_drive")
        if self.state.known_rule:
            events.append("rule_known")

        return {
            "agent_id": self.id,
            "lifecycle": self.state.lifecycle,
            "action": action,
            "obs": new_obs,
            "curiosity": round(self.state.curiosity_pressure, 3),
            "reproduction": round(self.state.reproduction_pressure, 3),
            "discoveries": self.state.discoveries,
            "events": events,
            "rule": self.state.known_rule,
        }

    def request_reproduction(self) -> Dict[str, Any]:
        proposal = {
            "parent_id": self.id,
            "genome": self.genome,
            "competence": self._competence(),
            "lifecycle": self.state.lifecycle,
            "discoveries": self.state.discoveries,
            "offspring_count": self.state.offspring_count,
        }
        if self.ccos is None:
            return {"approved": False, "reason": "no_ccos", "proposal": proposal}
        if hasattr(self.ccos, "evaluate_reproduction"):
            return self.ccos.evaluate_reproduction(proposal)
        return {"approved": False, "reason": "no_reproduction_api", "proposal": proposal}

    def _competence(self) -> float:
        return min(1.0, self.state.discoveries / 3.0 + self.state.successful_predictions / 20.0)

    def _update_lifecycle(self) -> None:
        e = self.state.experience
        if e >= self._thresholds.get("ADOLESCENT_to_MATURE", 10):
            self.state.lifecycle = "MATURE"
        elif e >= self._thresholds.get("CHILD_to_ADOLESCENT", 6):
            self.state.lifecycle = "ADOLESCENT"
        elif e >= self._thresholds.get("INFANT_to_CHILD", 3):
            self.state.lifecycle = "CHILD"
        else:
            self.state.lifecycle = "INFANT"

    def _update_curiosity(self, obs: Dict[str, Any]) -> None:
        w = float(self.genome.get("motivation_drive_weights", {}).get("curiosity", 0.8))
        if self.state.known_rule:
            self.state.curiosity_pressure = 0.15 * w
            return
        self.state.curiosity_pressure = min(1.0, (0.5 + 0.1 * len(self.episodic)) * w)

    def _update_reproduction(self) -> None:
        w = float(self.genome.get("motivation_drive_weights", {}).get("reproduction", 0.3))
        autonomy = float(self.genome.get("fixed_parameters", {}).get("autonomy_seeking", 0.5))
        stage = 1.0 if self.state.lifecycle in ("ADOLESCENT", "MATURE") else 0.0
        self.state.reproduction_pressure = min(
            1.0,
            stage
            * max(self._competence(), 0.4 if self.state.discoveries else 0.0)
            * autonomy
            * (0.8 + w),
        )

    def _choose_action(self, obs: Dict[str, Any]) -> str:
        if self.state.known_rule:
            return "WAIT" if self.state.experience % 3 == 0 else (
                "TOGGLE_A" if self.state.experience % 2 == 0 else "TOGGLE_B"
            )
        seq = ["TOGGLE_A", "TOGGLE_B", "WAIT", "TOGGLE_A", "TOGGLE_B"]
        return seq[self.state.experience % len(seq)]

    def _learn(self, before: Dict, action: str, after: Dict) -> None:
        self.episodic.append({"before": before, "action": action, "after": after})
        self.episodic = self.episodic[-50:]
        if self.state.known_rule:
            predicted = int(after["switch_a"]) ^ int(after["switch_b"])
            actual = int(after["lamp"])
            if predicted == actual:
                self.state.successful_predictions += 1
            else:
                self.state.failed_predictions += 1
            return
        if len(self.episodic) >= 5:
            ok = all(
                int(ep["after"]["lamp"])
                == (int(ep["after"]["switch_a"]) ^ int(ep["after"]["switch_b"]))
                for ep in self.episodic
            )
            if ok:
                rule = "lamp = switch_a XOR switch_b"
                self.state.known_rule = rule
                self.state.causal_rules.append(rule)
                self.state.discoveries += 1
