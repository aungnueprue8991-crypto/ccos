"""Observation Engine — normalize bound percepts into structured observation events."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts
from nexus.perception.binding import BoundPercept
from nexus.workspace.events import CogEvent, CogEventType


@dataclass
class StructuredObservation:
    observation_id: str = field(default_factory=new_id)
    text: str = ""
    domain: str = "general"
    predicted: Optional[float] = None
    actual: Optional[float] = None
    prediction_confidence: float = 0.5
    salience_hint: float = 0.5
    modalities: List[str] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=now_ts)
    provenance: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ObservationEngine:
    def normalize(
        self,
        percept: BoundPercept,
        domain: str = "general",
        predicted: Optional[float] = None,
        actual: Optional[float] = None,
        prediction_confidence: float = 0.5,
    ) -> StructuredObservation:
        return StructuredObservation(
            text=percept.text,
            domain=domain,
            predicted=predicted,
            actual=actual,
            prediction_confidence=prediction_confidence,
            salience_hint=min(1.0, 0.4 + 0.3 * len(percept.modalities) / 3.0),
            modalities=list(percept.modalities),
            features=dict(percept.features),
            provenance=[percept.percept_id, percept.source],
        )

    def to_event(self, obs: StructuredObservation) -> CogEvent:
        return CogEvent(
            type=CogEventType.OBSERVATION.value,
            payload=obs.to_dict(),
            source="observation_engine",
            priority=0.5,
            targets=["salience_engine", "cognitive_heart"],
        )
