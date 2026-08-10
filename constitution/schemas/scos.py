"""SCOS experiment, hypothesis, promotion objects. SCOS proposes; does not activate."""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class HypothesisStatus(str, Enum):
    GENERATED = "GENERATED"
    RANKED = "RANKED"
    TESTING = "TESTING"
    SUPPORTED = "SUPPORTED"
    FALSIFIED = "FALSIFIED"
    ARCHIVED = "ARCHIVED"


class Hypothesis(BaseModel):
    hypothesis_id: str = Field(default_factory=lambda: str(uuid4()))
    statement: str
    predictions: list[str] = Field(default_factory=list)
    domain: str = "general"
    status: HypothesisStatus = HypothesisStatus.GENERATED
    provenance: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Experiment(BaseModel):
    experiment_id: str = Field(default_factory=lambda: str(uuid4()))
    hypothesis_ref: Optional[str] = None
    code_version: str = ""
    capability_versions: list[str] = Field(default_factory=list)
    model_versions: list[str] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    random_seed: Optional[int] = None
    input_data_refs: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)
    verifier_result: Optional[str] = None
    reproducible: Optional[bool] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromotionCandidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid4()))
    capability_manifest_ref: str
    experiment_refs: list[str] = Field(default_factory=list)
    benchmark_results: dict[str, float] = Field(default_factory=dict)
    independent_verification: Optional[str] = None
    status: str = "CANDIDATE"
    lineage: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
