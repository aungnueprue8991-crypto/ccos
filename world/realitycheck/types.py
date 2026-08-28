"""RealityCheck typed objects — claims, experiments, verdicts."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts


class ClaimKind(str, Enum):
    SPECULATION = "SPECULATION"
    HYPOTHESIS = "HYPOTHESIS"
    PREDICTION = "PREDICTION"
    IMPLEMENTATION = "IMPLEMENTATION"
    EMPIRICAL = "EMPIRICAL"


class VerdictKind(str, Enum):
    SPECULATION = "SPECULATION"
    HYPOTHESIS = "HYPOTHESIS"
    SOURCE_SUPPORTED = "SOURCE-SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY-SUPPORTED"
    IMPLEMENTATION_VERIFIED = "IMPLEMENTATION-VERIFIED"
    REPRODUCTION_VERIFIED = "REPRODUCTION-VERIFIED"
    FALSIFIED = "FALSIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ADVERSARIAL_FAIL = "ADVERSARIAL-FAIL"


@dataclass
class Claim:
    claim_id: str = field(default_factory=new_id)
    statement: str = ""
    kind: ClaimKind = ClaimKind.HYPOTHESIS
    domain: str = "general"
    metrics: Dict[str, float] = field(default_factory=dict)
    baseline: Dict[str, float] = field(default_factory=dict)
    variables: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    source: str = "nexus"
    confidence_model: float = 0.0
    created_at: float = field(default_factory=now_ts)
    parent_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


@dataclass
class ExperimentSpec:
    spec_id: str = field(default_factory=new_id)
    claim_id: str = ""
    success_criteria: Dict[str, float] = field(default_factory=dict)
    baseline: Dict[str, float] = field(default_factory=dict)
    procedure: List[str] = field(default_factory=list)
    measurements: List[str] = field(default_factory=list)
    n_trials: int = 1
    adversarial_tests: List[str] = field(default_factory=list)
    cost_estimate: float = 1.0
    sandbox: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RealityVerdict:
    verdict_id: str = field(default_factory=new_id)
    claim_id: str = ""
    kind: VerdictKind = VerdictKind.INCONCLUSIVE
    measurements: Dict[str, float] = field(default_factory=dict)
    criteria_met: Dict[str, bool] = field(default_factory=dict)
    reproduction_pass: bool = False
    adversarial_pass: bool = False
    source_support: float = 0.0
    notes: List[str] = field(default_factory=list)
    evidence_chain: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=now_ts)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d
