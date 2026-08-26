"""Verdict Engine — combine verifier results into epistemic status.

CONFIDENCE ≠ EVIDENCE. Model confidence never upgrades verdict alone.
"""

from __future__ import annotations

from typing import List, Optional

from world.realitycheck.types import Claim, RealityVerdict, VerdictKind
from world.realitycheck.verifiers import VerifyResult


class VerdictEngine:
    def decide(
        self,
        claim: Claim,
        code: Optional[VerifyResult] = None,
        reproduction: Optional[VerifyResult] = None,
        adversarial: Optional[VerifyResult] = None,
        source: Optional[VerifyResult] = None,
        benchmark: Optional[VerifyResult] = None,
    ) -> RealityVerdict:
        notes: List[str] = []
        chain: List[str] = []
        measurements = {}
        criteria_met = {}

        if code:
            chain.append(f"code:{code.passed}")
            measurements.update(code.measurements)
            notes.extend(code.notes)
        if reproduction:
            chain.append(f"reproduction:{reproduction.passed}")
            measurements.update({f"repro_{k}": v for k, v in reproduction.measurements.items()})
            notes.extend(reproduction.notes)
        if adversarial:
            chain.append(f"adversarial:{adversarial.passed}")
            notes.extend(adversarial.notes)
        if source:
            chain.append(f"source:{source.passed}")
            measurements["source_support"] = source.measurements.get("source_support", 0.0)
            notes.extend(source.notes)
        if benchmark:
            chain.append(f"benchmark:{benchmark.passed}")
            measurements.update(benchmark.measurements)

        # Explicit: ignore claim.confidence_model for verdict kind
        notes.append(f"model_confidence_ignored={claim.confidence_model}")

        kind = VerdictKind.INCONCLUSIVE
        if code and code.passed and reproduction and reproduction.passed and (adversarial is None or adversarial.passed):
            kind = VerdictKind.REPRODUCTION_VERIFIED
        elif code and code.passed and (adversarial is None or adversarial.passed):
            kind = VerdictKind.IMPLEMENTATION_VERIFIED
        elif code and not code.passed:
            kind = VerdictKind.FALSIFIED
        elif adversarial and not adversarial.passed:
            kind = VerdictKind.ADVERSARIAL_FAIL
        elif source and source.passed and not code:
            kind = VerdictKind.SOURCE_SUPPORTED
        elif claim.kind.value == "SPECULATION" and not code:
            kind = VerdictKind.SPECULATION
        elif not code:
            kind = VerdictKind.HYPOTHESIS

        # criteria map from code notes if present
        for n in notes:
            if n.startswith("criteria="):
                criteria_met["parsed"] = True

        return RealityVerdict(
            claim_id=claim.claim_id,
            kind=kind,
            measurements=measurements,
            criteria_met=criteria_met,
            reproduction_pass=bool(reproduction and reproduction.passed),
            adversarial_pass=bool(adversarial is None or adversarial.passed),
            source_support=float(measurements.get("source_support", 0.0)),
            notes=notes,
            evidence_chain=chain,
        )
