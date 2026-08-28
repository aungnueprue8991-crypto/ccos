"""Curiosity engine — intrinsic motivation from novelty, uncertainty, prediction error."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ags.shared.types import Question, new_id, now_ts


@dataclass
class CuriositySignal:
    signal_id: str = field(default_factory=new_id)
    source: str = ""
    description: str = ""
    score: float = 0.0
    domain: str = "general"
    related_entity: str = ""
    timestamp: float = field(default_factory=now_ts)
    actionable: bool = True


class CuriosityEngine:
    def __init__(
        self,
        novelty_weight: float = 0.7,
        uncertainty_weight: float = 0.65,
        exploration_budget: float = 0.6,
        information_hunger: float = 0.7,
        surprise_sensitivity: float = 0.6,
    ):
        self.novelty_weight = novelty_weight
        self.uncertainty_weight = uncertainty_weight
        self.exploration_budget = exploration_budget
        self.information_hunger = information_hunger
        self.surprise_sensitivity = surprise_sensitivity
        self._seen_entities: set = set()
        self._signal_history: List[CuriositySignal] = []
        self._current_level: float = 0.5

    def score_observations(self, observations: List[Dict]) -> List[CuriositySignal]:
        signals: List[CuriositySignal] = []
        for obs in observations:
            signals.extend(self._score_single(obs))
        signals.sort(key=lambda s: s.score, reverse=True)
        self._signal_history.extend(signals[:5])
        self._signal_history = self._signal_history[-50:]
        return signals

    def score_prediction_errors(self, errors: List[Dict]) -> List[CuriositySignal]:
        signals = []
        for error in errors:
            surprise = float(error.get("surprise", 0.5))
            score = min(1.0, self.surprise_sensitivity * surprise * 1.5)
            signals.append(
                CuriositySignal(
                    source="prediction_error",
                    description=(
                        f"Predicted {error.get('predicted')} for "
                        f"{error.get('entity')}.{error.get('property')}, "
                        f"but observed {error.get('actual')}"
                    ),
                    score=score,
                    domain=str(error.get("entity", "unknown")),
                    related_entity=str(error.get("entity", "")),
                    actionable=score > 0.3,
                )
            )
        return signals

    def score_knowledge_gaps(self, gaps: List[str]) -> List[CuriositySignal]:
        return [
            CuriositySignal(
                source="knowledge_gap",
                description=gap,
                score=min(1.0, self.information_hunger * (0.6 + 0.4 * self.uncertainty_weight)),
                domain="epistemology",
                actionable=True,
            )
            for gap in gaps
        ]

    def score_novelty(self, entity_name: str, properties: Dict) -> float:
        if entity_name not in self._seen_entities:
            self._seen_entities.add(entity_name)
            return self.novelty_weight
        return self.novelty_weight * (1.0 / (1.0 + math.log(1 + len(properties))))

    def score_uncertainty(self, confidence: float) -> float:
        if confidence < 0.1:
            return self.uncertainty_weight * 0.3
        dist = abs(confidence - 0.4)
        return self.uncertainty_weight * max(0, 1 - 2 * dist)

    def get_exploration_drive(self) -> float:
        recent = [s for s in self._signal_history if now_ts() - s.timestamp < 60]
        if recent:
            avg = sum(s.score for s in recent) / len(recent)
            self._current_level = 0.7 * self._current_level + 0.3 * avg
        else:
            self._current_level = min(0.8, self._current_level + 0.05)
        return self._current_level

    def generate_questions(
        self, signals: List[CuriositySignal], agent_id: str
    ) -> List[Question]:
        questions = []
        for sig in signals[:3]:
            if sig.score < 0.3 or not sig.actionable:
                continue
            questions.append(
                Question(
                    agent_id=agent_id,
                    text=self._signal_to_question(sig),
                    domain=sig.domain,
                    urgency=sig.score,
                    source=sig.source,
                )
            )
        return questions

    def get_top_signal(self) -> Optional[CuriositySignal]:
        recent = [s for s in self._signal_history if now_ts() - s.timestamp < 300]
        return max(recent, key=lambda s: s.score) if recent else None

    def _score_single(self, obs: Dict) -> List[CuriositySignal]:
        signals = []
        entity = str(obs.get("entity", obs.get("source", "unknown")))
        domain = str(obs.get("domain", "general"))
        novelty = self.score_novelty(entity, obs)
        if novelty > 0.2:
            signals.append(
                CuriositySignal(
                    source="novelty",
                    description=f"Novel observation: {entity}",
                    score=novelty,
                    domain=domain,
                    related_entity=entity,
                    actionable=True,
                )
            )
        unc = self.score_uncertainty(float(obs.get("confidence", 0.5)))
        if unc > 0.25:
            signals.append(
                CuriositySignal(
                    source="uncertainty",
                    description=f"Uncertain observation about {entity}",
                    score=unc,
                    domain=domain,
                    related_entity=entity,
                    actionable=unc > 0.4,
                )
            )
        return signals

    def _signal_to_question(self, sig: CuriositySignal) -> str:
        if sig.source == "prediction_error":
            return f"Why did observation differ from prediction? {sig.description}"
        if sig.source == "knowledge_gap":
            return f"How can I fill this knowledge gap? {sig.description}"
        if sig.source == "novelty":
            return f"What is {sig.related_entity} and what rules govern it?"
        if sig.source == "uncertainty":
            return f"What evidence would resolve uncertainty about {sig.related_entity}?"
        return f"What explains: {sig.description[:100]}?"
