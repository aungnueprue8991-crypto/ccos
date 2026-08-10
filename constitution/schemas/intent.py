"""First-class Intent objects. Root intents are immutable (CCOS-011)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class IntentStatus(str, Enum):
    DRAFT = "DRAFT"
    COMMITTED = "COMMITTED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


class Intent(BaseModel):
    intent_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_intent: Optional[str] = None
    root_intent: Optional[str] = None
    issuer: str
    objective: str
    constraints: list[str] = Field(default_factory=list)
    authorization: Optional[str] = None
    priority: int = 0
    deadline: Optional[datetime] = None
    provenance: list[str] = Field(default_factory=list)
    status: IntentStatus = IntentStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    immutable_root: bool = False

    model_config = {"extra": "forbid"}
