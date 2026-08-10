"""Capability manifests and lifecycle. SCOS proposes; Governance + COS activate."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CapabilityLifecycle(str, Enum):
    DISCOVERED = "DISCOVERED"
    PROPOSED = "PROPOSED"
    REGISTERED = "REGISTERED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    REVOKED = "REVOKED"


class CapabilityManifest(BaseModel):
    capability_id: str = Field(default_factory=lambda: str(uuid4()))
    version: str = "0.1.0"
    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    resource_requirements: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    verification_status: str = "UNVERIFIED"
    lifecycle_status: CapabilityLifecycle = CapabilityLifecycle.DISCOVERED
    implementation_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fitness_vector: dict[str, float] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}
