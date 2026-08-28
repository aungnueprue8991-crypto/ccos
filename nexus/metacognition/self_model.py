"""Self-model / Q-vector and calibration updates."""

from __future__ import annotations

from typing import List, Optional

from nexus.types import QVector, StrategyGenome


class MetaCognition:
    def __init__(self):
        self.q = QVector()
        self.prediction_log: List[dict] = []
        self.strategies: List[StrategyGenome] = []

    def predict_success(self, task: str, base: float = 0.6) -> float:
        p = base * (0.5 + 0.5 * self.q.confidence)
        self.prediction_log.append({"task": task, "predicted": p})
        return p

    def observe_outcome(self, task: str, success: bool) -> None:
        predicted = 0.5
        for row in reversed(self.prediction_log):
            if row["task"] == task:
                predicted = float(row["predicted"])
                break
        actual = 1.0 if success else 0.0
        err = abs(predicted - actual)
        new_cal = 0.8 * self.q.calibration + 0.2 * (1.0 - err)
        new_conf = 0.9 * self.q.confidence + 0.1 * actual
        new_cap = 0.9 * self.q.capability + 0.1 * actual
        self.q.update(
            calibration=new_cal,
            confidence=new_conf,
            capability=new_cap,
            uncertainty=err,
            failure_prediction=err if not success else self.q.failure_prediction * 0.9,
            self_prediction=1.0 - err,
        )

    def register_strategy(self, genome: StrategyGenome) -> None:
        self.strategies.append(genome)

    def best_strategy(self) -> Optional[StrategyGenome]:
        if not self.strategies:
            return None
        return max(self.strategies, key=lambda s: s.fitness)
