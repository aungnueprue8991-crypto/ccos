"""Drive arbitration — select next cognitive objective from competing drives."""

from __future__ import annotations

from typing import Dict, List, Optional

from nexus.drives.signals import DriveSensors
from nexus.types import CognitiveObjective, DriveName, DriveSignal, QVector


_PRIORITY = {
    DriveName.SURPRISE: 1.15,
    DriveName.COHERENCE: 1.12,
    DriveName.CURIOSITY: 1.1,
    DriveName.SELF_IMPROVEMENT: 1.05,
    DriveName.AGENCY: 1.0,
    DriveName.CHALLENGE: 0.95,
    DriveName.NOVELTY: 0.95,
    DriveName.COMPRESSION: 0.9,
    DriveName.CREATIVITY: 0.85,
    DriveName.MASTERY: 0.8,
    DriveName.HUMILITY: 0.75,
    DriveName.CONSERVATION: 0.7,
}


class DriveManager:
    def __init__(self):
        self.sensors = DriveSensors()
        self.history: List[CognitiveObjective] = []

    def evaluate(
        self,
        observations=None,
        prediction_errors=None,
        contradictions=None,
        archive_size: int = 0,
        recent_novelty: float = 0.0,
        competence: float = 0.5,
        resource_pressure: float = 0.2,
        q: Optional[QVector] = None,
    ) -> CognitiveObjective:
        signals = self.sensors.sense(
            observations=observations,
            prediction_errors=prediction_errors,
            contradictions=contradictions,
            archive_size=archive_size,
            recent_novelty=recent_novelty,
            competence=competence,
            resource_pressure=resource_pressure,
            q=q,
        )
        return self.arbitrate(signals, resource_pressure=resource_pressure)

    def arbitrate(
        self,
        signals: List[DriveSignal],
        resource_pressure: float = 0.2,
    ) -> CognitiveObjective:
        if not signals:
            return CognitiveObjective(
                primary_drive=DriveName.CURIOSITY,
                description="default explore",
                priority=0.3,
            )

        scored: Dict[DriveName, float] = {}
        rationales: Dict[DriveName, str] = {}
        for s in signals:
            w = _PRIORITY.get(s.name, 1.0)
            if s.name in (
                DriveName.CREATIVITY,
                DriveName.CHALLENGE,
                DriveName.AGENCY,
            ):
                w *= max(0.3, 1.0 - 0.5 * resource_pressure)
            scored[s.name] = s.intensity * w
            rationales[s.name] = s.rationale

        winner = max(scored, key=lambda k: scored[k])
        intensity = scored[winner]
        obj = CognitiveObjective(
            primary_drive=winner,
            description=f"pursue {winner.value}: {rationales.get(winner, '')}",
            priority=min(1.0, intensity),
            budget=max(0.2, 1.0 - resource_pressure),
        )
        self.history.append(obj)
        self.history = self.history[-100:]
        return obj
