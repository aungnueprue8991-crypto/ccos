"""Cross-domain transfer — predict success/failure from structural similarity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from nexus.patterns.fingerprint import FingerprintEngine
from nexus.patterns.similarity import fingerprint_similarity
from nexus.types import StructuralFingerprint, Theory


@dataclass
class TransferHypothesis:
    source_domain: str
    target_domain: str
    mechanism: str
    similarity: float
    predicted_success: float
    predicted_failure_modes: List[str]
    rationale: str


class TransferEngine:
    def __init__(self):
        self.fp = FingerprintEngine()

    def propose(
        self,
        theory: Theory,
        source_fp: StructuralFingerprint,
        target_fp: StructuralFingerprint,
    ) -> TransferHypothesis:
        sim = fingerprint_similarity(source_fp, target_fp, metric="weighted_l1")
        success = sim * theory.confidence
        failures = []
        if sim < 0.4:
            failures.append("low structural similarity")
        if source_fp.features.get("causal_structure", 0) > 0.7 and target_fp.features.get(
            "causal_structure", 0
        ) < 0.3:
            failures.append("causal structure mismatch")
        return TransferHypothesis(
            source_domain=source_fp.domain,
            target_domain=target_fp.domain,
            mechanism=theory.mechanism,
            similarity=round(sim, 4),
            predicted_success=round(success, 4),
            predicted_failure_modes=failures,
            rationale=(
                f"transfer '{theory.mechanism}' from {source_fp.domain} → "
                f"{target_fp.domain} (sim={sim:.2f})"
            ),
        )
