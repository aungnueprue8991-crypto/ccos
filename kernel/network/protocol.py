"""N2.2/N2.3 — Signed replication protocol + conflict policy."""

from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class ConflictAction(str, Enum):
    APPEND = "APPEND"
    IDEMPOTENT_ACCEPT = "IDEMPOTENT_ACCEPT"
    REQUEST_MISSING = "REQUEST_MISSING"
    QUARANTINE = "QUARANTINE"
    REJECT = "REJECT"


class ReplicationRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    sender_node: str
    receiver_node: str
    chain_id: str = "primary"
    from_sequence: int = 0
    to_sequence: Optional[int] = None
    event_batch: List[dict[str, Any]] = Field(default_factory=list)
    previous_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signature: str = ""

    def canonical_bytes(self) -> bytes:
        data = {
            "request_id": self.request_id, "sender_node": self.sender_node,
            "receiver_node": self.receiver_node, "chain_id": self.chain_id,
            "from_sequence": self.from_sequence, "to_sequence": self.to_sequence,
            "event_batch": self.event_batch, "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode()

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


class ReplicationResponse(BaseModel):
    request_id: str
    receiver_node: str
    action: ConflictAction
    accepted: int = 0
    rejected: int = 0
    missing_from: Optional[int] = None
    message: str = ""
    quarantine_id: Optional[str] = None
    chain_valid: bool = True
    head_sequence: int = 0
    head_hash: Optional[str] = None


class HeadInfo(BaseModel):
    node_id: str
    name: str
    sequence: int
    last_hash: Optional[str] = None
    chain_valid: bool = True
    public_key: str = ""
    trust_state: str = "PROVISIONED"


def classify_batch(local_count: int, local_last_hash: Optional[str],
                   batch: List[dict], requested_from: int) -> ConflictAction:
    if not batch:
        return ConflictAction.IDEMPOTENT_ACCEPT
    sequences = [e.get("sequence") for e in batch if e.get("sequence") is not None]
    if not sequences:
        return ConflictAction.REJECT
    min_seq, max_seq = min(sequences), max(sequences)
    if min_seq > local_count:
        return ConflictAction.REQUEST_MISSING
    first = batch[0]
    prev = first.get("previous_event_hash")
    if min_seq == local_count and local_last_hash and prev and prev != local_last_hash:
        return ConflictAction.QUARANTINE
    if max_seq < local_count:
        return ConflictAction.IDEMPOTENT_ACCEPT
    return ConflictAction.APPEND
