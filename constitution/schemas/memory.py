"""Memory Governance — all writes pass through policy + provenance (blueprint §10)."""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from .event import EpistemicStatus


class MemoryKind(str, Enum):
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    WORKING = "WORKING"
    INSTITUTIONAL = "INSTITUTIONAL"
    SCIENTIFIC = "SCIENTIFIC"
    CONSTITUTIONAL = "CONSTITUTIONAL"


class MemoryRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid4()))
    namespace: str
    kind: MemoryKind
    content: dict[str, Any] = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)
    epistemic_status: EpistemicStatus = EpistemicStatus.UNVERIFIED
    access_policy: list[str] = Field(default_factory=list)
    retention: str = "permanent"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    writer: str = ""
