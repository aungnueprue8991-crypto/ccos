"""SCOS Experiment Runner — reproducible, seeded, observable."""

from __future__ import annotations

import random
import time
from typing import Any, Callable, Dict, Optional

from constitution.schemas.scos import Experiment
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class ExperimentRunner:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger

    def run(
        self,
        experiment: Experiment,
        fn: Callable[[Dict[str, Any]], Dict[str, float]],
    ) -> Experiment:
        """Execute experiment function under controlled seed and record metrics."""
        seed = experiment.random_seed if experiment.random_seed is not None else 42
        random.seed(seed)
        start = time.time()
        try:
            metrics = fn(experiment.parameters)
            experiment.metrics = {**experiment.metrics, **metrics}
            experiment.reproducible = True
            status = "success"
        except Exception as e:
            experiment.metrics["error"] = 1.0
            experiment.reproducible = False
            status = f"failed:{e}"
        duration = time.time() - start
        experiment.metrics["duration_s"] = duration

        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="scos.experiment.completed",
                    producer_id="scos.runner",
                    payload={
                        "experiment_id": experiment.experiment_id,
                        "status": status,
                        "metrics": experiment.metrics,
                        "seed": seed,
                    },
                )
            )
        return experiment
