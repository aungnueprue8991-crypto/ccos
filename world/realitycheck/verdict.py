"""Verdict Engine — map evidence to VerdictKind; never trust model confidence alone."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from world.realitycheck.types import Claim, RealityVerdict, VerdictKind


class VerdictEngine:
    def decide(
        self,
        claim: Claim,
        *,
        observed: Optional[Dict[str, Any]] = None,
        expected: Optional[Dict[str, Any]] = None,
        thresholds: Optional[Dict[str, float]] = None,
        source_supported: bool = False,
        reproduced: bool = False,
        falsified: bool = False,
        evidence: Optional[List[str]] = None,
        notes: str = "",
        experiment_id: Optional[str] = None,
    ) -> RealityVerdict:
        evidence = list(evidence or [])
        observed = observed or {}
        expected = expected or {}
        thresholds = thresholds or {}

        if falsified:
            return RealityVerdict(
                claim_id=claim.claim_id,
                kind=VerdictKind.FALSIFIED,
                evidence=evidence or ["falsified_by_experiment"],
                metrics=observed,
                notes=notes or "evidence contradicts claim",
                experiment_id=experiment_id,
            )

        if not observed and not source_supported:
            return RealityVerdict(
                claim_id=claim.claim_id,
                kind=VerdictKind.UNVERIFIED,
                evidence=evidence,
                metrics={},
                notes=notes or "insufficient evidence",
                experiment_id=experiment_id,
            )

        if observed and expected:
            ok = True
            for k, exp_v in expected.items():
                if k not in observed:
                    ok = False
                    break
                thr = thresholds.get(k)
                if thr is not None:
                    try:
                        if abs(float(observed[k]) - float(exp_v)) > float(thr):
                            ok = False
                            break
                    except (TypeError, ValueError):
                        if observed[k] != exp_v:
                            ok = False
                            break
                elif observed[k] != exp_v:
                    ok = False
                    break
            if ok:
                kind = (
                    VerdictKind.REPRODUCTION_VERIFIED
                    if reproduced
                    else VerdictKind.IMPLEMENTATION_VERIFIED
                )
                return RealityVerdict(
                    claim_id=claim.claim_id,
                    kind=kind,
                    evidence=evidence or ["metrics_within_threshold"],
                    metrics=observed,
                    notes=notes,
                    experiment_id=experiment_id,
                )
            return RealityVerdict(
                claim_id=claim.claim_id,
                kind=VerdictKind.INCONCLUSIVE,
                evidence=evidence or ["metrics_mismatch"],
                metrics=observed,
                notes=notes or "observed did not match expected",
                experiment_id=experiment_id,
            )

        if source_supported:
            return RealityVerdict(
                claim_id=claim.claim_id,
                kind=VerdictKind.SOURCE_SUPPORTED,
                evidence=evidence or ["external_source"],
                metrics=observed,
                notes=notes,
                experiment_id=experiment_id,
            )

        return RealityVerdict(
            claim_id=claim.claim_id,
            kind=VerdictKind.HYPOTHESIS,
            evidence=evidence,
            metrics=observed,
            notes=notes or "claim remains a hypothesis",
            experiment_id=experiment_id,
        )
