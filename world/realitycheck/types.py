"""RealityCheck core types — claims, experiments, verdicts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time
import uuid


class VerdictKind(str, Enum):
    SPECULATION = "speculation"
    HYPOTHESIS = "hypothesis"
    IMPLEMENTATION_VERIFIED = "implementation_verified"
    SOURCE_SUPPORTED = "source_supported"
    REPRODUCTION_VERIFIED = "reproduction_verified"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"
    UNVERIFIED = "unverified"


@dataclass
class Claim:
    statement: str
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    domain: str = "general"
    falsifiable: bool = True
    metrics: Dict[str, Any] = field(default_factory=dict)
    provenance: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class ExperimentSpec:
    name: str
    method: str
    expected: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])


@dataclass
class RealityVerdict:
    claim_id: str
    kind: VerdictKind
    evidence: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    experiment_id: Optional[str] = None
    ts: float = field(default_factory=time.time)
