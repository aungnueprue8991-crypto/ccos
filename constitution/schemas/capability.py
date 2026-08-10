"""Capability manifests, permissions, and lifecycle (N1 Execution Fabric)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CapabilityLifecycle(str, Enum):
    UNREGISTERED = "UNREGISTERED"
    DISCOVERED = "DISCOVERED"
    REGISTERED = "REGISTERED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    SANDBOXED = "SANDBOXED"
    ACTIVE = "ACTIVE"
    TRUSTED = "TRUSTED"
    DEPRECATED = "DEPRECATED"
    REVOKED = "REVOKED"
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"


class CapabilityPermission(str, Enum):
    READ_WEB = "READ_WEB"
    WRITE_FILE = "WRITE_FILE"
    READ_FILE = "READ_FILE"
    READ_REPO = "READ_REPO"
    WRITE_REPO = "WRITE_REPO"
    EXECUTE_CODE = "EXECUTE_CODE"
    NETWORK_ACCESS = "NETWORK_ACCESS"
    MEMORY_WRITE = "MEMORY_WRITE"
    DEPLOY = "DEPLOY"
    COMMUNICATE = "COMMUNICATE"
    COMPUTE = "COMPUTE"
    READ_ONLY = "READ_ONLY"


ALLOWED_TRANSITIONS: dict[CapabilityLifecycle, set[CapabilityLifecycle]] = {
    CapabilityLifecycle.UNREGISTERED: {CapabilityLifecycle.DISCOVERED, CapabilityLifecycle.REGISTERED},
    CapabilityLifecycle.DISCOVERED: {CapabilityLifecycle.REGISTERED, CapabilityLifecycle.REVOKED},
    CapabilityLifecycle.REGISTERED: {CapabilityLifecycle.VALIDATED, CapabilityLifecycle.APPROVED, CapabilityLifecycle.REVOKED},
    CapabilityLifecycle.VALIDATED: {CapabilityLifecycle.APPROVED, CapabilityLifecycle.REVOKED},
    CapabilityLifecycle.APPROVED: {CapabilityLifecycle.SANDBOXED, CapabilityLifecycle.DEPRECATED, CapabilityLifecycle.REVOKED},
    CapabilityLifecycle.SANDBOXED: {CapabilityLifecycle.ACTIVE, CapabilityLifecycle.APPROVED, CapabilityLifecycle.REVOKED, CapabilityLifecycle.DEPRECATED},
    CapabilityLifecycle.ACTIVE: {CapabilityLifecycle.TRUSTED, CapabilityLifecycle.DEPRECATED, CapabilityLifecycle.REVOKED, CapabilityLifecycle.SANDBOXED},
    CapabilityLifecycle.TRUSTED: {CapabilityLifecycle.DEPRECATED, CapabilityLifecycle.REVOKED, CapabilityLifecycle.ACTIVE},
    CapabilityLifecycle.DEPRECATED: {CapabilityLifecycle.REVOKED, CapabilityLifecycle.APPROVED},
    CapabilityLifecycle.REVOKED: set(),
    CapabilityLifecycle.PROPOSED: {CapabilityLifecycle.REGISTERED, CapabilityLifecycle.APPROVED, CapabilityLifecycle.REVOKED},
    CapabilityLifecycle.VERIFIED: {CapabilityLifecycle.APPROVED, CapabilityLifecycle.SANDBOXED, CapabilityLifecycle.REVOKED},
}


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
    adapter_id: Optional[str] = None
    domain: str = "general"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fitness_vector: dict[str, float] = Field(default_factory=dict)
    sandbox_profile: dict[str, Any] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}


class CapabilityResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid4()))
    capability_id: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0
    resource_used: dict[str, float] = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)
    observation_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CapabilityObservation(BaseModel):
    observation_id: str = Field(default_factory=lambda: str(uuid4()))
    capability_id: str
    result_id: str
    metrics: dict[str, float] = Field(default_factory=dict)
    side_effects: list[str] = Field(default_factory=list)
    verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
