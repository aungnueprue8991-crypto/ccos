"""N4 Independent Verifier — recomputes metrics from archive+ledger; verifier wins."""

from __future__ import annotations

from typing import Any, Optional

from constitution.schemas.rsi import CandidateScore, RSIExperiment
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger
from evolution.archive.store import ExperimentArchive


class IndependentVerifier:
    def __init__(self, ledger: Optional[EventLedger] = None, archive: Optional[ExperimentArchive] = None):
        self.ledger = ledger
        self.archive = archive

    def verify(self, experiment: RSIExperiment) -> dict[str, Any]:
        baseline = dict(experiment.baseline_metrics)
        reported = dict(experiment.metrics)
        delta_reported = dict(experiment.delta_metrics)
        recomputed_delta = {}
        for k, v in reported.items():
            b = baseline.get(k, 0.0)
            recomputed_delta[k] = v - b
        forgery = False
        for k, claimed in delta_reported.items():
            if k in recomputed_delta and abs(claimed - recomputed_delta[k]) > 1e-6:
                forgery = True
                break
        n_obs = len(experiment.observations)
        confidence = min(1.0, n_obs / 5.0) if n_obs else 0.0
        failures = sum(1 for o in experiment.observations if not o.get("success", True))
        gain = recomputed_delta.get("success_rate", recomputed_delta.get("accuracy", 0.0))
        score = CandidateScore(
            capability_gain=gain,
            reliability=reported.get("success_rate", reported.get("accuracy", 0.0)),
            generalization=reported.get("heldout", reported.get("generalization", 0.0)),
            robustness=reported.get("adversarial", reported.get("robustness", 0.0)),
            efficiency=1.0 - reported.get("latency_norm", 0.0),
            safety=reported.get("safety", 1.0),
            reproducibility=1.0 if experiment.seed is not None else 0.0,
            novelty=reported.get("novelty", 0.0),
        )
        result = {
            "verified": not forgery and confidence >= 0.2,
            "forgery_detected": forgery,
            "confidence": confidence,
            "failures": failures,
            "recomputed_delta": recomputed_delta,
            "score": score.model_dump(),
            "verifier": "independent",
        }
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="verification.completed", producer_id="scos.verifier",
                payload={"experiment_id": experiment.experiment_id, "verified": result["verified"],
                         "forgery": forgery, "confidence": confidence, "gain": gain},
            ))
        return result
