"""Global Cognitive Workspace — shared blackboard for the ecology.

Engines publish/read here. Attention/drives gate what is broadcast widely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from nexus.workspace.events import CogEvent


@dataclass
class CognitiveState:
    uncertainty: float = 0.5
    curiosity: float = 0.5
    novelty_pressure: float = 0.3
    contradiction: float = 0.0
    confidence: float = 0.5
    exploration_budget: float = 0.5
    exploitation_pressure: float = 0.3
    unresolved_questions: int = 0
    active_theories: int = 0
    surprise: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "uncertainty": self.uncertainty,
            "curiosity": self.curiosity,
            "novelty_pressure": self.novelty_pressure,
            "contradiction": self.contradiction,
            "confidence": self.confidence,
            "exploration_budget": self.exploration_budget,
            "exploitation_pressure": self.exploitation_pressure,
            "unresolved_questions": float(self.unresolved_questions),
            "active_theories": float(self.active_theories),
            "surprise": self.surprise,
        }


@dataclass
class WorkspaceSnapshot:
    state: CognitiveState
    observations: List[Dict[str, Any]] = field(default_factory=list)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)
    questions: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    theories: List[Dict[str, Any]] = field(default_factory=list)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    simulations: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    attention: List[str] = field(default_factory=list)


class GlobalWorkspace:
    """Competitive broadcast bus + shared temporary cognitive content."""

    def __init__(self, max_log: int = 500):
        self.state = CognitiveState()
        self.observations: List[Dict[str, Any]] = []
        self.thoughts: List[Dict[str, Any]] = []
        self.questions: List[Dict[str, Any]] = []
        self.hypotheses: List[Dict[str, Any]] = []
        self.theories: List[Dict[str, Any]] = []
        self.anomalies: List[Dict[str, Any]] = []
        self.simulations: List[Dict[str, Any]] = []
        self.evidence: List[Dict[str, Any]] = []
        self.attention: List[str] = []
        self.event_log: List[CogEvent] = []
        self.max_log = max_log
        self._subscribers: Dict[str, List] = {}

    def update_state(self, **kwargs: float) -> CognitiveState:
        for k, v in kwargs.items():
            if hasattr(self.state, k):
                if k in ("unresolved_questions", "active_theories"):
                    setattr(self.state, k, int(v))
                else:
                    setattr(self.state, k, float(v))
        return self.state

    def publish(self, event: CogEvent) -> CogEvent:
        self.event_log.append(event)
        if len(self.event_log) > self.max_log:
            self.event_log = self.event_log[-self.max_log :]
        t = event.type
        p = event.payload
        if "anomaly" in t:
            self.anomalies.append(p)
        elif "thought" in t:
            self.thoughts.append(p)
        elif "question" in t:
            self.questions.append(p)
            self.state.unresolved_questions = len(self.questions)
        elif "hypothesis" in t:
            self.hypotheses.append(p)
        elif "theory" in t:
            self.theories.append(p)
            self.state.active_theories = len(self.theories)
        elif "simulation" in t:
            self.simulations.append(p)
        elif "evidence" in t or t.endswith("support") or t.endswith("falsify"):
            self.evidence.append(p)
        elif "observation" in t:
            self.observations.append(p)
        for key, handlers in list(self._subscribers.items()):
            if key == "*" or key == t or t.startswith(key.rstrip("*")):
                for h in handlers:
                    h(event)
        return event

    def subscribe(self, event_prefix: str, handler) -> None:
        self._subscribers.setdefault(event_prefix, []).append(handler)

    def broadcast(self, event: CogEvent, engines: List[str]) -> CogEvent:
        event.targets = list(engines)
        self.attention = list(engines)
        return self.publish(event)

    def snapshot(self) -> WorkspaceSnapshot:
        return WorkspaceSnapshot(
            state=CognitiveState(**self.state.as_dict()),
            observations=list(self.observations[-20:]),
            thoughts=list(self.thoughts[-20:]),
            questions=list(self.questions[-20:]),
            hypotheses=list(self.hypotheses[-20:]),
            theories=list(self.theories[-20:]),
            anomalies=list(self.anomalies[-20:]),
            simulations=list(self.simulations[-20:]),
            evidence=list(self.evidence[-20:]),
            attention=list(self.attention),
        )
