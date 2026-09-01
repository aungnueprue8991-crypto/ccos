"""Claim registry for RealityCheck."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from .types import RCClaim, ClaimStatus, _id, _now

class ClaimRegistry:
    def __init__(self) -> None:
        self._claims: Dict[str, RCClaim] = {}

    def register(self, statement: str, **kwargs: Any) -> RCClaim:
        claim_id = kwargs.get("claim_id") or _id("C")
        claim = RCClaim(claim_id=claim_id, statement=statement, **{k: v for k, v in kwargs.items() if k != "claim_id"})
        self._claims[claim.claim_id] = claim
        return claim

    def get(self, claim_id: str) -> Optional[RCClaim]:
        return self._claims.get(claim_id)

    def update_status(self, claim_id: str, status: ClaimStatus) -> Optional[RCClaim]:
        c = self._claims.get(claim_id)
        if not c:
            return None
        c.status = status
        c.updated_at = _now()
        return c

    def list(self, status: Optional[ClaimStatus] = None) -> List[RCClaim]:
        vals = list(self._claims.values())
        if status is not None:
            return [c for c in vals if c.status == status]
        return vals

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for c in self._claims.values():
            key = c.status.value if hasattr(c.status, "value") else str(c.status)
            out[key] = out.get(key, 0) + 1
        out["total"] = len(self._claims)
        return out
