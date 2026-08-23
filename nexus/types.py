"""Shared NEXUS types — ideas, questions, theories, strategies, Q-vector."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts


class DriveName(str, Enum):
    CURIOSITY = "curiosity"
    MASTERY = "mastery"
    NOVELTY = "novelty"
    COHERENCE = "coherence"
    COMPRESSION = "compression"
    AGENCY = "agency"
    CHALLENGE = "challenge"
    CREATIVITY = "creativity"
    SELF_IMPROVEMENT = "self_improvement"
    CONSERVATION = "conservation"
    HUMILITY = "humility"
    SURPRISE = "surprise"


@dataclass
class DriveSignal:
    name: DriveName
    intensity: float
    rationale: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveObjective:
    objective_id: str = field(default_factory=new_id)
    primary_drive: DriveName = DriveName.CURIOSITY
    description: str = ""
    priority: float = 0.5
    budget: float = 1.0
    domain: str = "general"
    created_at: float = field(default_factory=now_ts)


class QuestionKind(str, Enum):
    ANOMALY = "anomaly"
    CONTRADICTION = "contradiction"
    GAP = "gap"
    CAPABILITY = "capability"
    BOUNDARY = "boundary"
    COMPRESSION = "compression"
    TRANSFER = "transfer"
    SELF_MODEL = "self_model"


@dataclass
class ResearchQuestion:
    question_id: str = field(default_factory=new_id)
    kind: QuestionKind = QuestionKind.ANOMALY
    text: str = ""
    domain: str = "general"
    novelty: float = 0.5
    informativeness: float = 0.5
    solvability: float = 0.5
    utility: float = 0.5
    cost: float = 0.3
    source_drive: Optional[DriveName] = None
    context: Dict[str, Any] = field(default_factory=dict)
    accepted: bool = False

    def score(self) -> float:
        return (
            0.25 * self.novelty
            + 0.25 * self.informativeness
            + 0.2 * self.solvability
            + 0.2 * self.utility
            - 0.15 * self.cost
        )


@dataclass
class Idea:
    idea_id: str = field(default_factory=new_id)
    concepts: List[str] = field(default_factory=list)
    mechanisms: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    analogies: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)
    operator: str = "combine"
    novelty_score: float = 0.5
    text: str = ""
    domain: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Hypothesis:
    hypothesis_id: str = field(default_factory=new_id)
    statement: str = ""
    predictions: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    falsifiers: List[str] = field(default_factory=list)
    idea_id: Optional[str] = None
    question_id: Optional[str] = None
    status: str = "proposed"


@dataclass
class Theory:
    theory_id: str = field(default_factory=new_id)
    mechanism: str = ""
    boundary_conditions: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    abstractions: List[str] = field(default_factory=list)
    domain: str = "general"
    confidence: float = 0.5


@dataclass
class StructuralFingerprint:
    domain: str
    features: Dict[str, float]
    labels: List[str] = field(default_factory=list)

    def distance(self, other: "StructuralFingerprint") -> float:
        keys = set(self.features) | set(other.features)
        if not keys:
            return 1.0
        acc = 0.0
        for k in keys:
            acc += abs(self.features.get(k, 0.0) - other.features.get(k, 0.0))
        return acc / len(keys)


@dataclass
class QVector:
    capability: float = 0.5
    confidence: float = 0.5
    uncertainty: float = 0.5
    calibration: float = 0.5
    learning_rate: float = 0.5
    transfer_ability: float = 0.5
    reasoning_efficiency: float = 0.5
    creativity: float = 0.5
    exploration_efficiency: float = 0.5
    failure_prediction: float = 0.5
    self_prediction: float = 0.5

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)

    def update(self, **kwargs: float) -> None:
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, max(0.0, min(1.0, float(v))))


@dataclass
class IntelligenceVector:
    performance: float = 0.0
    learning: float = 0.0
    generality: float = 0.0
    reasoning: float = 0.0
    creativity: float = 0.0
    metacognition: float = 0.0
    autonomy: float = 0.0
    open_endedness: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class StrategyGenome:
    strategy_id: str = field(default_factory=new_id)
    name: str = ""
    pipeline: List[str] = field(default_factory=list)
    traits: Dict[str, float] = field(default_factory=dict)
    fitness: float = 0.0
    archive_cell: Optional[str] = None
