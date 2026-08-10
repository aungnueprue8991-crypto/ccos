"""Agent vs Citizen distinction (blueprint §20)."""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class CitizenStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class Agent(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid4()))
    identity: str
    runtime_ref: Optional[str] = None
    capabilities: list[str] = Field(default_factory=list)
    memory_namespace: str = "default"
    execution_history: list[str] = Field(default_factory=list)
    state: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Citizen(BaseModel):
    citizen_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_ref: str
    organization: str
    role: str
    permissions: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    rights: list[str] = Field(default_factory=list)
    governance_status: CitizenStatus = CitizenStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Organization(BaseModel):
    org_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    members: list[str] = Field(default_factory=list)
    roles: dict[str, list[str]] = Field(default_factory=dict)
    authority: list[str] = Field(default_factory=list)
    resources: dict = Field(default_factory=dict)
    policies: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    treasury: dict = Field(default_factory=dict)
    memory_namespace: str = "org"
    capabilities: list[str] = Field(default_factory=list)
    governance: dict = Field(default_factory=dict)
