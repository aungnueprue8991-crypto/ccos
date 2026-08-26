"""Evidence Gate — epistemic firewall; LLM text is never knowledge by itself."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts


class BeliefStatus(str, Enum):
    UNTESTED = "UNTESTED"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    FALSIFIED = "FALSIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"
    STALE = "STALE"


@dataclass
class ClaimRecord:
    claim_id: str = field(default_factory=new_id)
    statement: str = ""
    status: BeliefStatus = BeliefStatus.UNTESTED
    confidence: float = 0.3
    predictions: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    last_verified: float = field(default_factory=now_ts)
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "status": self.status.value,
            "confidence": self.confidence,
            "predictions": self.predictions,
            "evidence_ids": self.evidence_ids,
            "assumptions": self.assumptions,
            "last_verified": self.last_verified,
            "source": self.source,
        }


class EvidenceGate:
    def __init__(self):
        self.claims: Dict[str, ClaimRecord] = {}

    def register(self, statement: str, source: str = "", predictions: Optional[List[str]] = None) -> ClaimRecord:
        c = ClaimRecord(statement=statement, source=source, predictions=list(predictions or []))
        self.claims[c.claim_id] = c
        return c

    def assess(
        self,
        claim_id: str,
        *,
        oracle_accepted: Optional[bool] = None,
        prediction_match: Optional[float] = None,
        contradicted: bool = False,
    ) -> ClaimRecord:
        c = self.claims[claim_id]
        if contradicted:
            c.status = BeliefStatus.FALSIFIED if (prediction_match is not None and prediction_match < 0.2) else BeliefStatus.CONTRADICTED
            c.confidence = max(0.05, c.confidence * 0.4)
        elif oracle_accepted is True or (prediction_match is not None and prediction_match >= 0.8):
            c.status = BeliefStatus.SUPPORTED
            c.confidence = min(0.95, max(c.confidence, 0.7) + 0.1)
        elif prediction_match is not None and prediction_match >= 0.5:
            c.status = BeliefStatus.PARTIALLY_SUPPORTED
            c.confidence = min(0.75, c.confidence + 0.05)
        elif oracle_accepted is False:
            c.status = BeliefStatus.FALSIFIED
            c.confidence = max(0.05, c.confidence * 0.3)
        else:
            c.status = BeliefStatus.INCONCLUSIVE
        c.last_verified = now_ts()
        return c
