"""Activation rules — competitive selection for the global workspace.

Rules emit CogEvents; they do not run engines themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from nexus.workspace.blackboard import CognitiveState, GlobalWorkspace
from nexus.workspace.events import CogEvent, CogEventType


@dataclass
class Observation:
    id: str
    predicted_value: float
    actual_value: float
    prediction_confidence: float
    salience: float
    source: str = "world"
    entity: str = ""
    domain: str = "general"


def anomaly_score(obs: Observation, state: CognitiveState) -> float:
    prediction_error = abs(obs.actual_value - obs.predicted_value)
    err_n = min(1.0, prediction_error)
    confidence_gap = 1.0 - obs.prediction_confidence
    return (
        0.45 * err_n
        + 0.25 * obs.salience
        + 0.20 * confidence_gap
        + 0.10 * state.uncertainty
    )


class ActivationRules:
    """Declarative activation rules for the cognitive ecology."""

    def __init__(
        self,
        anomaly_threshold: float = 0.55,
        multi_theory_min: int = 2,
        structure_min_episodes: int = 2,
    ):
        self.anomaly_threshold = anomaly_threshold
        self.multi_theory_min = multi_theory_min
        self.structure_min_episodes = structure_min_episodes

    def anomaly_rule(
        self, obs: Observation, state: CognitiveState
    ) -> List[CogEvent]:
        score = anomaly_score(obs, state)
        if score < self.anomaly_threshold:
            return []
        payload = {
            "observation_id": obs.id,
            "score": round(score, 4),
            "salience": obs.salience,
            "prediction_error": abs(obs.actual_value - obs.predicted_value),
            "confidence": obs.prediction_confidence,
            "entity": obs.entity or obs.id,
            "domain": obs.domain,
            "source": obs.source,
        }
        return [
            CogEvent(
                type=CogEventType.ANOMALY.value,
                payload=payload,
                source="activation_rules.anomaly",
                targets=[
                    "question_engine",
                    "pattern_engine",
                    "curiosity_engine",
                    "memory_service",
                ],
                priority=score,
            ),
            CogEvent(
                type=CogEventType.ENGINE_WAKE.value,
                payload={
                    "engines": [
                        "question_engine",
                        "pattern_engine",
                        "curiosity_engine",
                        "thought_engine",
                    ],
                    "reason": "anomaly",
                    "score": score,
                },
                source="activation_rules.anomaly",
                priority=score,
            ),
        ]

    def question_rule(
        self, problem: str, assumption_confidence: float, state: CognitiveState
    ) -> List[CogEvent]:
        if assumption_confidence >= 0.7 and state.uncertainty < 0.6:
            return []
        return [
            CogEvent(
                type=CogEventType.QUESTION.value,
                payload={
                    "text": f"Why assume this problem framing: {problem[:120]}?",
                    "kind": "question_about_question",
                    "assumption_confidence": assumption_confidence,
                },
                source="activation_rules.question",
                targets=["question_engine", "thought_engine"],
                priority=0.6 + 0.2 * (1.0 - assumption_confidence),
            )
        ]

    def hypothesis_rule(self, n_candidates: int, state: CognitiveState) -> List[CogEvent]:
        if n_candidates < 1:
            return []
        return [
            CogEvent(
                type=CogEventType.ENGINE_WAKE.value,
                payload={
                    "engines": ["hypothesis_engine", "simulation_engine", "prediction_engine"],
                    "reason": "candidates_available",
                    "n": n_candidates,
                },
                source="activation_rules.hypothesis",
                priority=0.55,
            )
        ]

    def competition_rule(self, n_theories: int) -> List[CogEvent]:
        if n_theories < self.multi_theory_min:
            return []
        return [
            CogEvent(
                type=CogEventType.THEORY_COMPETE.value,
                payload={"n_theories": n_theories},
                source="activation_rules.competition",
                targets=["theory_competition", "evidence_gate"],
                priority=0.7,
            )
        ]

    def experiment_rule(self, theories_tied: bool, budget: float) -> List[CogEvent]:
        if not theories_tied or budget < 0.1:
            return []
        return [
            CogEvent(
                type=CogEventType.EXPERIMENT.value,
                payload={"reason": "theories_tied", "budget": budget},
                source="activation_rules.experiment",
                targets=["experiment_manager", "tool_service"],
                priority=0.75,
            )
        ]

    def abstraction_rule(self, shared_structure_count: int) -> List[CogEvent]:
        if shared_structure_count < self.structure_min_episodes:
            return []
        return [
            CogEvent(
                type=CogEventType.ABSTRACTION.value,
                payload={"episodes": shared_structure_count},
                source="activation_rules.abstraction",
                targets=["abstraction_engine", "transfer_engine"],
                priority=0.65,
            )
        ]

    def serendipity_rule(
        self, structural_sim: float, semantic_sim: float, threshold: float = 0.5
    ) -> List[CogEvent]:
        if structural_sim < threshold or semantic_sim > 0.4:
            return []
        return [
            CogEvent(
                type=CogEventType.SERENDIPITY.value,
                payload={
                    "structural_sim": structural_sim,
                    "semantic_sim": semantic_sim,
                },
                source="activation_rules.serendipity",
                targets=["serendipity_engine", "analogy_engine", "thought_engine"],
                priority=0.6 + 0.3 * structural_sim,
            )
        ]

    def meta_rule(self, repeated_winner: Optional[str], streak: int) -> List[CogEvent]:
        if not repeated_winner or streak < 3:
            return []
        return [
            CogEvent(
                type=CogEventType.META.value,
                payload={"module": repeated_winner, "streak": streak},
                source="activation_rules.meta",
                targets=["self_model", "meta_cognition"],
                priority=0.5,
            )
        ]

    def apply_anomaly_to_workspace(
        self, ws: GlobalWorkspace, obs: Observation
    ) -> List[CogEvent]:
        events = self.anomaly_rule(obs, ws.state)
        for ev in events:
            if ev.type == CogEventType.ANOMALY.value:
                ws.update_state(
                    surprise=float(ev.payload.get("score", 0.5)),
                    uncertainty=min(1.0, ws.state.uncertainty + 0.1),
                    curiosity=min(1.0, ws.state.curiosity + 0.15),
                )
            ws.broadcast(ev, ev.targets or [])
        return events
