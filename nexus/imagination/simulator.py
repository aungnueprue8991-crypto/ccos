"""Imagination / counterfactual engine — simulate before real experiment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ImaginedOutcome:
    action: str
    predicted_result: Dict[str, Any]
    expected_information_gain: float
    risk: float = 0.2


class ImaginationEngine:
    """Lightweight world-model rollouts (not full physics — planning aid)."""

    def counterfactuals(
        self,
        state: Dict[str, Any],
        actions: List[str],
        model: Optional[Any] = None,
    ) -> List[ImaginedOutcome]:
        outcomes: List[ImaginedOutcome] = []
        baseline = float(state.get("uncertainty", 0.5))
        for i, action in enumerate(actions):
            interventional = any(
                k in action.lower() for k in ("intervene", "perturb", "set", "fork")
            )
            ig = 0.4 + 0.15 * i
            if interventional:
                ig += 0.25
            risk = 0.15 + (0.2 if interventional else 0.05)
            pred = {
                "uncertainty_after": max(0.05, baseline - ig * 0.3),
                "action": action,
            }
            outcomes.append(
                ImaginedOutcome(
                    action=action,
                    predicted_result=pred,
                    expected_information_gain=min(1.0, ig),
                    risk=risk,
                )
            )
        outcomes.sort(key=lambda o: o.expected_information_gain - 0.3 * o.risk, reverse=True)
        return outcomes

    def select_informative(
        self, state: Dict[str, Any], actions: List[str]
    ) -> Optional[ImaginedOutcome]:
        outs = self.counterfactuals(state, actions)
        return outs[0] if outs else None
