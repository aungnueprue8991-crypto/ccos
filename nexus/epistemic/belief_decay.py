"""Belief Decay — time-sensitive confidence reduction for stale knowledge."""

from __future__ import annotations

import time
from typing import Dict

from nexus.epistemic.evidence_gate import BeliefStatus, ClaimRecord


class BeliefDecayEngine:
    def __init__(self, half_life_seconds: float = 86400.0):
        self.half_life = half_life_seconds

    def decay(self, claim: ClaimRecord, now: float | None = None) -> ClaimRecord:
        now = now or time.time()
        age = max(0.0, now - claim.last_verified)
        # exponential decay toward 0.2 floor for non-supported; supported decays slower
        factor = 0.5 ** (age / self.half_life)
        if claim.status == BeliefStatus.SUPPORTED:
            factor = 0.5 ** (age / (self.half_life * 3))
        claim.confidence = max(0.05, claim.confidence * factor)
        if claim.confidence < 0.25 and claim.status == BeliefStatus.SUPPORTED:
            claim.status = BeliefStatus.STALE
        return claim

    def decay_all(self, claims: Dict[str, ClaimRecord]) -> int:
        n = 0
        for c in claims.values():
            before = c.confidence
            self.decay(c)
            if c.confidence < before:
                n += 1
        return n
