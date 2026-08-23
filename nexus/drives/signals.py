"""Drive sensors — map world/self state into drive intensities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.types import DriveName, DriveSignal, QVector


class DriveSensors:
    def sense(
        self,
        observations: Optional[List[Dict[str, Any]]] = None,
        prediction_errors: Optional[List[Dict[str, Any]]] = None,
        contradictions: Optional[List[str]] = None,
        archive_size: int = 0,
        recent_novelty: float = 0.0,
        competence: float = 0.5,
        resource_pressure: float = 0.2,
        q: Optional[QVector] = None,
    ) -> List[DriveSignal]:
        observations = observations or []
        prediction_errors = prediction_errors or []
        contradictions = contradictions or []
        q = q or QVector()
        signals: List[DriveSignal] = []
        if prediction_errors:
            avg_s = sum(float(e.get("surprise", 0.5)) for e in prediction_errors) / len(prediction_errors)
            signals.append(DriveSignal(DriveName.SURPRISE, min(1.0, avg_s), f"{len(prediction_errors)} prediction errors", {"n": len(prediction_errors)}))
            signals.append(DriveSignal(DriveName.CURIOSITY, min(1.0, 0.4 + 0.6 * avg_s), "uncertainty x surprise"))
        else:
            signals.append(DriveSignal(DriveName.CURIOSITY, 0.25, "baseline curiosity"))
            signals.append(DriveSignal(DriveName.SURPRISE, 0.1, "no recent errors"))
        nov = max(recent_novelty, 0.15 if archive_size < 5 else 0.05)
        signals.append(DriveSignal(DriveName.NOVELTY, min(1.0, nov), f"archive_size={archive_size}"))
        signals.append(DriveSignal(DriveName.MASTERY, competence, f"competence={competence:.2f}"))
        coh = min(1.0, 0.5 + 0.15 * len(contradictions)) if contradictions else 0.15
        signals.append(DriveSignal(DriveName.COHERENCE, coh, f"contradictions={len(contradictions)}"))
        n_obs = len(observations)
        signals.append(DriveSignal(DriveName.COMPRESSION, min(1.0, n_obs / 20.0) if n_obs else 0.1, f"observations={n_obs}"))
        signals.append(DriveSignal(DriveName.AGENCY, min(1.0, 0.3 + 0.5 * q.uncertainty), "act to gain information"))
        challenge = max(0.0, competence * (1.0 - nov) * 0.9)
        signals.append(DriveSignal(DriveName.CHALLENGE, challenge, "slightly beyond competence"))
        creativity = max(0.1, (1.0 - competence) * 0.3 + (1.0 - nov) * 0.4)
        signals.append(DriveSignal(DriveName.CREATIVITY, min(1.0, creativity), "explore combinations"))
        cal_gap = abs(q.confidence - q.capability)
        signals.append(DriveSignal(DriveName.SELF_IMPROVEMENT, min(1.0, 0.2 + cal_gap), f"calibration_gap={cal_gap:.2f}"))
        signals.append(DriveSignal(DriveName.CONSERVATION, min(1.0, resource_pressure), f"resource_pressure={resource_pressure:.2f}"))
        hum = min(1.0, 0.3 + 0.5 * q.uncertainty + 0.2 * (1.0 - q.calibration))
        signals.append(DriveSignal(DriveName.HUMILITY, hum, "likelihood of being wrong"))
        return signals
