"""Evidence Planner — what must be measured to decide a claim."""

from __future__ import annotations

from world.realitycheck.types import Claim, ExperimentSpec


class EvidencePlanner:
    def plan(self, claim: Claim) -> ExperimentSpec:
        criteria = dict(claim.metrics)
        if not criteria:
            criteria = {"success_rate_min": 0.7}

        procedure = [
            "record_baseline",
            "apply_intervention",
            "measure_metrics",
            "compare_to_criteria",
            "reproduce",
            "adversarial_probe",
        ]
        measurements = list(criteria.keys()) + list(claim.variables)
        adversarial = ["noise_injection", "subset_holdout"]
        if "compression" in claim.statement.lower() or "compression_ratio_min" in criteria:
            adversarial.append("retrieval_fidelity_stress")

        return ExperimentSpec(
            claim_id=claim.claim_id,
            success_criteria=criteria,
            baseline=dict(claim.baseline),
            procedure=procedure,
            measurements=list(dict.fromkeys(measurements)),
            n_trials=max(1, 2 if claim.kind.value != "SPECULATION" else 1),
            adversarial_tests=adversarial,
            cost_estimate=1.0 + 0.2 * len(criteria),
            sandbox=True,
        )
