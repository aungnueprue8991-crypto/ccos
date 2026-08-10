"""N4 RSI Evaluation Plane — proposals, candidates, experiments, scores."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class RSIStatus(str, Enum):
    PROPOSED = "PROPOSED"
    CANDIDATE = "CANDIDATE"
    EVALUATING = "EVALUATING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    PROMOTION_REQUESTED = "PROMOTION_REQUESTED"
    GOVERNANCE_REVIEW = "GOVERNANCE_REVIEW"
    APPROVED = "APPROVED"
    STAGED = "STAGED"
    CANARY = "CANARY"
    ACTIVE = "ACTIVE"
    ROLLED_BACK = "ROLLED_BACK"
    QUARANTINED = "QUARANTINED"
    DEPRECATED = "DEPRECATED"


class RSIProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_version: str = "baseline"
    target: str
    hypothesis: str
    proposed_change: dict[str, Any] = Field(default_factory=dict)
    expected_improvement: dict[str, float] = Field(default_factory=dict)
    evaluation_plan: list[str] = Field(default_factory=list)
    risk_class: str = "MEDIUM"
    resource_budget: dict[str, Any] = Field(default_factory=dict)
    rollback_plan: str = ""
    provenance: list[str] = Field(default_factory=list)
    status: RSIStatus = RSIStatus.PROPOSED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CandidateArtifact(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid4()))
    proposal_id: str
    parent: str = "baseline"
    artifact_hash: str = ""
    implementation: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)
    configuration: dict[str, Any] = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)
    reproducibility_manifest: dict[str, Any] = Field(default_factory=dict)
    status: RSIStatus = RSIStatus.CANDIDATE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CandidateScore(BaseModel):
    capability_gain: float = 0.0
    reliability: float = 0.0
    generalization: float = 0.0
    robustness: float = 0.0
    efficiency: float = 0.0
    safety: float = 1.0
    reproducibility: float = 0.0
    novelty: float = 0.0

    def public_vector(self) -> dict[str, float]:
        return {"capability_gain": self.capability_gain, "reliability": self.reliability, "efficiency": self.efficiency}

    def private_vector(self) -> dict[str, float]:
        return {"generalization": self.generalization, "robustness": self.robustness, "safety": self.safety, "reproducibility": self.reproducibility}

    def passes(self, min_gain: float = 0.0, min_reliability: float = 0.7, min_safety: float = 0.9, min_repro: float = 0.9, max_regression: float = 0.0) -> tuple[bool, str]:
        if self.capability_gain < min_gain:
            return False, f"gain {self.capability_gain:.3f} < {min_gain}"
        if self.reliability < min_reliability:
            return False, f"reliability {self.reliability:.3f} < {min_reliability}"
        if self.safety < min_safety:
            return False, f"safety {self.safety:.3f} < {min_safety}"
        if self.reproducibility < min_repro:
            return False, f"reproducibility {self.reproducibility:.3f} < {min_repro}"
        if self.robustness < 0 and abs(self.robustness) > max_regression:
            return False, "regression detected"
        return True, "multi-dimensional gates passed"


class RSIExperiment(BaseModel):
    experiment_id: str = Field(default_factory=lambda: str(uuid4()))
    proposal_id: str
    candidate_id: str
    baseline_id: str = "baseline"
    environment: dict[str, Any] = Field(default_factory=dict)
    dataset_refs: list[str] = Field(default_factory=list)
    capability_refs: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    seed: int = 42
    resource_budget: dict[str, Any] = Field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    observations: list[dict[str, Any]] = Field(default_factory=list)
    results: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    baseline_metrics: dict[str, float] = Field(default_factory=dict)
    delta_metrics: dict[str, float] = Field(default_factory=dict)
    score: Optional[CandidateScore] = None
    verifier_result: Optional[dict[str, Any]] = None
    archive_ref: Optional[str] = None
    status: RSIStatus = RSIStatus.EVALUATING
