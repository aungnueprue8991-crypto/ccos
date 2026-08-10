"""CCOS EventEnvelope — the atomic unit of the Observatory / Event Spine."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EpistemicStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VALIDATING = "VALIDATING"
    SUPPORTED = "SUPPORTED"
    CORROBORATED = "CORROBORATED"
    VERIFIED = "VERIFIED"
    CONTESTED = "CONTESTED"
    REJECTED = "REJECTED"


class EventEnvelope(BaseModel):
    """Typed, signed, hash-chained event that everything communicates through."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    schema_version: str = "1.0.0"
    producer_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sequence: Optional[int] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    payload_hash: Optional[str] = None
    previous_event_hash: Optional[str] = None
    provenance: list[str] = Field(default_factory=list)
    signature: Optional[str] = None

    model_config = {"extra": "forbid"}


class Evidence(BaseModel):
    """Provenance-aware evidence object. Observation ≠ Truth."""

    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    claim: str
    source: str
    observation_refs: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    methodology: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    independent_support: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    verification_state: EpistemicStatus = EpistemicStatus.UNVERIFIED
    epistemic_status: EpistemicStatus = EpistemicStatus.UNVERIFIED

    model_config = {"extra": "forbid"}
