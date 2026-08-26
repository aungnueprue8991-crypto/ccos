"""Typed cognitive events for the NEXUS event-driven ecology."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts


class CogEventType(str, Enum):
    OBSERVATION = "observation.received"
    ANOMALY = "anomaly.detected"
    ENGINE_WAKE = "engine.wake"
    THOUGHT = "thought.emitted"
    QUESTION = "question.emitted"
    PATTERN = "pattern.detected"
    HYPOTHESIS = "hypothesis.proposed"
    THEORY_COMPETE = "theory.competition"
    PREDICTION = "prediction.made"
    SIMULATION = "simulation.completed"
    EXPERIMENT = "experiment.requested"
    EVIDENCE = "evidence.assessed"
    SUPPORT = "evidence.support"
    FALSIFY = "evidence.falsify"
    INCONCLUSIVE = "evidence.inconclusive"
    HYP_EVOLVE = "hypothesis.evolved"
    ABSTRACTION = "abstraction.extracted"
    TRANSFER = "transfer.proposed"
    SERENDIPITY = "serendipity.link"
    CONCEPT = "concept.formed"
    META = "meta.policy_update"
    STATE = "state.update"
    WORKSPACE_BROADCAST = "workspace.broadcast"


@dataclass
class CogEvent:
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=new_id)
    source: str = ""
    targets: List[str] = field(default_factory=list)
    priority: float = 0.5
    timestamp: float = field(default_factory=now_ts)
    parent_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
