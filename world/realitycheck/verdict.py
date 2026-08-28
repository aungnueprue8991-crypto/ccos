"""VerdictEngine — combine verifier results into RealityVerdict."""

from __future__ import annotations

from typing import Any, Optional

from world.realitycheck.types import Claim, RealityVerdict, VerdictKind


class VerdictEngine:
    def decide(
        self,
        claim: Claim,
        code: Any = None,
        reproduction: Any = None,
        adversarial: Any = None,
        source: Any = None,
        benchmark: Any = None,
    ) -> RealityVerdict:
        chain = []
        notes = []
        measurements = {}
        criteria_met = {}

        if code:
            chain.append(f"code:{code.passed}")
            measurements.update(getattr(code, "measurements", {}) or {})
            notes.extend(getattr(code, "notes", []) or [])
        if reproduction:
            chain.append(f"reproduction:{reproduction.passed}")
            measurements.update(
                {f"repro_{k}": v for k, v in (getattr(reproduction, "measurements", {}) or {}).items()}
            )
            notes.extend(getattr(reproduction, "notes", []) or [])
        if adversarial:
            chain.append(f"adversarial:{adversarial.passed}")
            notes.extend(getattr(adversarial, "notes", []) or [])
        if source:
            chain.append(f"source:{source.passed}")
            measurements["source_support"] = getattr(source, "measurements", {}).get("source_support", 0.0)
            notes.extend(getattr(source, "notes", []) or [])
        if benchmark:
            chain.append(f"benchmark:{benchmark.passed}")
            measurements.update(getattr(benchmark, "measurements", {}) or {})

        notes.append(f"model_confidence_ignored={claim.confidence_model}")

        kind = VerdictKind.INCONCLUSIVE
        if code and code.passed and reproduction and reproduction.passed and (
            adversarial is None or adversarial.passed
        ):
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
