"""N3 central object — InvocationEnvelope + AuthorizationDecision."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class RiskClass(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuthorizationDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    allowed: bool
    reason: str = ""
    issuer: str = "cos.execution_gate"
    capability_id: str = ""
    invocation_id: str = ""
    permissions_granted: list[str] = Field(default_factory=list)
    resource_limits: dict[str, Any] = Field(default_factory=dict)
    risk_class: RiskClass = RiskClass.LOW
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}


class InvocationEnvelope(BaseModel):
    """Single object binding intent → capability → authorization → execution."""

    invocation_id: str = Field(default_factory=lambda: str(uuid4()))
    capability_id: str
    capability_version: str = "0.1.0"
    issuer: str = ""
    agent_id: Optional[str] = None
    citizen_role: Optional[str] = None
    intent_id: Optional[str] = None
    authorization_id: Optional[str] = None
    input_payload: dict[str, Any] = Field(default_factory=dict)
    input_hash: str = ""
    resource_policy: dict[str, Any] = Field(default_factory=dict)
    execution_policy: dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    provenance: list[str] = Field(default_factory=list)
    risk_class: RiskClass = RiskClass.LOW
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}

    def compute_input_hash(self) -> str:
        raw = json.dumps(self.input_payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def bind_input(self) -> "InvocationEnvelope":
        self.input_hash = self.compute_input_hash()
        return self
