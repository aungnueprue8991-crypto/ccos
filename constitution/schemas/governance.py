"""Governance control plane objects."""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    EVALUATING = "EVALUATING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    ROLLED_BACK = "ROLLED_BACK"


class Proposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    proposer: str
    title: str
    description: str = ""
    proposal_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    status: ProposalStatus = ProposalStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision_ref: Optional[str] = None


class Decision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    proposal_id: str
    decision_maker: str
    outcome: str
    rationale: str = ""
    policy_versions: list[str] = Field(default_factory=list)
    evidence_considered: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attributable: bool = True
