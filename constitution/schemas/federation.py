"""N5 Federation Plane — civilization identity, treaties, requests."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CivTrustState(str, Enum):
    UNKNOWN = "UNKNOWN"
    DISCOVERED = "DISCOVERED"
    IDENTIFIED = "IDENTIFIED"
    ATTESTED = "ATTESTED"
    REGISTERED = "REGISTERED"
    VALIDATED = "VALIDATED"
    FEDERATED = "FEDERATED"
    TRUSTED_PARTNER = "TRUSTED_PARTNER"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"


class FederationOp(str, Enum):
    DISCOVER = "DISCOVER"
    ATTEST = "ATTEST"
    NEGOTIATE = "NEGOTIATE"
    SHARE_KNOWLEDGE = "SHARE_KNOWLEDGE"
    SHARE_CAPABILITY = "SHARE_CAPABILITY"
    REQUEST_EXECUTION = "REQUEST_EXECUTION"
    JOINT_EXPERIMENT = "JOINT_EXPERIMENT"
    TRANSFER_ARTIFACT = "TRANSFER_ARTIFACT"
    AUDIT = "AUDIT"
    REVOKE = "REVOKE"


class CivilizationIdentity(BaseModel):
    civilization_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    root_identity: str = ""
    constitution_hash: str = ""
    protocol_version: str = "n5.1"
    capability_summary: list[str] = Field(default_factory=list)
    governance_summary: str = "local_sovereign"
    public_keys: dict[str, str] = Field(default_factory=dict)
    federation_policy: dict[str, Any] = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FederationTreaty(BaseModel):
    treaty_id: str = Field(default_factory=lambda: str(uuid4()))
    parties: list[str] = Field(default_factory=list)
    scope: str = "general"
    permissions: list[str] = Field(default_factory=list)
    obligations: list[str] = Field(default_factory=list)
    resource_commitments: dict[str, Any] = Field(default_factory=dict)
    data_rules: dict[str, Any] = Field(default_factory=dict)
    capability_rules: dict[str, Any] = Field(default_factory=dict)
    experiment_rules: dict[str, Any] = Field(default_factory=dict)
    dispute_rules: dict[str, Any] = Field(default_factory=dict)
    expiration: Optional[datetime] = None
    revocation: Optional[str] = None
    signatures: dict[str, str] = Field(default_factory=dict)
    status: str = "proposed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FederationRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    federation_id: str = Field(default_factory=lambda: str(uuid4()))
    sender_civilization: str
    receiver_civilization: str
    request_type: FederationOp
    intent: str = ""
    capabilities_requested: list[str] = Field(default_factory=list)
    resources_requested: dict[str, Any] = Field(default_factory=dict)
    policy_requirements: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    expiry: Optional[datetime] = None
    nonce: str = Field(default_factory=lambda: str(uuid4()))
    signature: str = ""
    provenance: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FederationResponse(BaseModel):
    request_id: str
    decision: str
    granted_scope: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    expiration: Optional[datetime] = None
    obligations: list[str] = Field(default_factory=list)
    signature: str = ""
    provenance: list[str] = Field(default_factory=list)
    message: str = ""


class EvidencePackage(BaseModel):
    package_id: str = Field(default_factory=lambda: str(uuid4()))
    source_civilization: str
    claims: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    methodology: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)
    signature: str = ""
