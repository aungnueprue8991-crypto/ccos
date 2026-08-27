"""Validation hooks — make routing scientifically testable."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from nexus.workspace.events import CogEvent


@dataclass
class HookResult:
    name: str
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)


class ValidationHooks:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def pre_activation(
        self,
        event: CogEvent,
        budget: float,
        seen_ids: Optional[set] = None,
        safety_ok: bool = True,
    ) -> HookResult:
        seen_ids = seen_ids or set()
        reasons = []
        ok = True
        if event.priority < 0.05:
            ok = False
            reasons.append("priority_too_low")
        if budget <= 0:
            ok = False
            reasons.append("no_budget")
        if event.event_id in seen_ids:
            ok = False
            reasons.append("duplicate")
        if not safety_ok:
            ok = False
            reasons.append("safety_block")
        result = HookResult(
            "pre_activation",
            ok,
            {"reasons": reasons, "event_type": event.type, "budget": budget},
        )
        self.history.append({"hook": "pre", **result.details, "passed": ok})
        return result

    def post_activation(
        self,
        event: CogEvent,
        downstream: Dict[str, Any],
    ) -> HookResult:
        details = {
            "event_type": event.type,
            "question_was_woken": bool(downstream.get("question_engine")),
            "pattern_was_woken": bool(downstream.get("pattern_engine")),
            "memory_was_queried": bool(downstream.get("memory_queried")),
            "hypothesis_changed": bool(downstream.get("hypothesis_updated")),
            "new_question": bool(downstream.get("new_question")),
            "information_gain": float(downstream.get("information_gain", 0.0)),
        }
        if event.type.endswith("anomaly.detected"):
            passed = details["question_was_woken"] or details["pattern_was_woken"]
        else:
            passed = True
        result = HookResult("post_activation", passed, details)
        self.history.append({"hook": "post", **details, "passed": passed})
        return result

    def validate_anomaly_event(
        self, event: Dict[str, Any], downstream_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "event_emitted": event.get("type") == "anomaly.detected",
            "question_was_woken": "question_engine" in downstream_results.get("engines", [])
            or downstream_results.get("question_engine", False),
            "memory_was_queried": downstream_results.get("memory_queried", False),
            "hypothesis_changed": downstream_results.get("hypothesis_updated", False),
        }

    def ablation_compare(
        self, with_engine: Dict[str, float], without_engine: Dict[str, float]
    ) -> HookResult:
        keys = ("novelty", "transfer", "falsification", "experiment_efficiency")
        deltas = {k: with_engine.get(k, 0) - without_engine.get(k, 0) for k in keys}
        passed = any(v > 0 for v in deltas.values())
        return HookResult("ablation", passed, {"deltas": deltas})

    def calibration(
        self, predicted_confidence: float, actual_success: bool
    ) -> HookResult:
        actual = 1.0 if actual_success else 0.0
        err = abs(predicted_confidence - actual)
        return HookResult(
            "calibration",
            err <= 0.5,
            {"predicted": predicted_confidence, "actual": actual, "error": err},
        )

    def lineage(
        self, parent_id: str, child_id: str, relation: str = "evolved_from"
    ) -> HookResult:
        return HookResult(
            "lineage",
            bool(parent_id and child_id),
            {"parent": parent_id, "child": child_id, "relation": relation},
        )

    def novelty(
        self,
        lexical: float,
        structural: float,
        mechanistic: float,
        predictive: float,
    ) -> HookResult:
        genuine = structural >= 0.5 or mechanistic >= 0.5 or predictive >= 0.5
        return HookResult(
            "novelty",
            genuine,
            {
                "lexical": lexical,
                "structural": structural,
                "mechanistic": mechanistic,
                "predictive": predictive,
                "genuine": genuine,
            },
        )
