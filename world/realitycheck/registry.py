"""Claim Registry — all claims with lineage; confidence ≠ evidence."""

from __future__ import annotations

from typing import Dict, List, Optional

from world.realitycheck.types import Claim, RealityVerdict, VerdictKind


class ClaimRegistry:
    def __init__(self):
        self.claims: Dict[str, Claim] = {}
        self.verdicts: Dict[str, RealityVerdict] = {}  # claim_id -> latest

    def register(self, claim: Claim) -> Claim:
        self.claims[claim.claim_id] = claim
        return claim

    def get(self, claim_id: str) -> Optional[Claim]:
        return self.claims.get(claim_id)

    def attach_verdict(self, verdict: RealityVerdict) -> None:
        self.verdicts[verdict.claim_id] = verdict

    def latest_verdict(self, claim_id: str) -> Optional[RealityVerdict]:
        return self.verdicts.get(claim_id)

    def by_status(self, kind: VerdictKind) -> List[Claim]:
        out = []
        for cid, v in self.verdicts.items():
            if v.kind == kind and cid in self.claims:
                out.append(self.claims[cid])
        return out

    def knowledge_only(self) -> List[Claim]:
        """Only implementation-verified or reproduction-verified claims."""
        allowed = {
            VerdictKind.IMPLEMENTATION_VERIFIED,
            VerdictKind.REPRODUCTION_VERIFIED,
            VerdictKind.SOURCE_SUPPORTED,
        }
        out = []
        for cid, v in self.verdicts.items():
            if v.kind in allowed and cid in self.claims:
                out.append(self.claims[cid])
        return out
