"""Reproduction governance — explicit policy, no silent auto-spawn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ReproductionPolicy:
    min_competence: float = 0.3
    min_discoveries: int = 1
    max_offspring_per_agent: int = 3
    require_adolescent: bool = True
    enable_policy_approval: bool = True


class LivingReproductionGate:
    def __init__(self, policy: Optional[ReproductionPolicy] = None, ccos_client: Any = None):
        self.policy = policy or ReproductionPolicy()
        self.ccos = ccos_client
        self.decisions: list = []

    def evaluate_reproduction(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        p = self.policy
        competence = float(proposal.get("competence") or 0)
        discoveries = int(proposal.get("discoveries") or 0)
        lifecycle = proposal.get("lifecycle") or "INFANT"
        offspring = int(proposal.get("offspring_count") or 0)

        if not p.enable_policy_approval:
            out = {"approved": False, "reason": "policy_disabled", "proposal": proposal}
            self.decisions.append(out)
            return out
        if p.require_adolescent and lifecycle not in ("ADOLESCENT", "MATURE"):
            out = {"approved": False, "reason": "lifecycle_too_young", "proposal": proposal}
            self.decisions.append(out)
            return out
        if competence < p.min_competence:
            out = {"approved": False, "reason": "low_competence", "proposal": proposal}
            self.decisions.append(out)
            return out
        if discoveries < p.min_discoveries:
            out = {"approved": False, "reason": "insufficient_discoveries", "proposal": proposal}
            self.decisions.append(out)
            return out
        if offspring >= p.max_offspring_per_agent:
            out = {"approved": False, "reason": "max_offspring", "proposal": proposal}
            self.decisions.append(out)
            return out

        from ags.living.genome import mutate

        child = mutate(proposal["genome"])
        out = {
            "approved": True,
            "reason": "policy_thresholds_met",
            "proposal": proposal,
            "child_genome": child,
        }
        self.decisions.append(out)
        return out
