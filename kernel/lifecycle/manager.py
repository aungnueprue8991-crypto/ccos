"""COS Lifecycle Manager — process/runtime entity lifecycle."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class EntityState(str, Enum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


class ManagedEntity(BaseModel):
    entity_id: str = Field(default_factory=lambda: str(uuid4()))
    kind: str
    name: str
    state: EntityState = EntityState.CREATED
    owner: str = ""
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LifecycleManager:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._entities: Dict[str, ManagedEntity] = {}
        self._lock = threading.RLock()

    def create(self, kind: str, name: str, owner: str = "", metadata: dict | None = None) -> ManagedEntity:
        entity = ManagedEntity(kind=kind, name=name, owner=owner, metadata=metadata or {})
        with self._lock:
            self._entities[entity.entity_id] = entity
        self._emit("cos.lifecycle.created", entity)
        return entity

    def transition(self, entity_id: str, new_state: EntityState, reason: str = "") -> ManagedEntity:
        with self._lock:
            entity = self._entities[entity_id]
            old = entity.state
            allowed = {
                EntityState.CREATED: {EntityState.STARTING, EntityState.TERMINATED},
                EntityState.STARTING: {EntityState.RUNNING, EntityState.FAILED},
                EntityState.RUNNING: {EntityState.STOPPING, EntityState.FAILED},
                EntityState.STOPPING: {EntityState.STOPPED, EntityState.FAILED},
                EntityState.STOPPED: {EntityState.STARTING, EntityState.TERMINATED},
                EntityState.FAILED: {EntityState.STARTING, EntityState.TERMINATED},
                EntityState.TERMINATED: set(),
            }
            if new_state not in allowed.get(old, set()):
                raise ValueError(f"Invalid lifecycle transition {old.value} → {new_state.value}")
            entity.state = new_state
            entity.updated_at = datetime.now(timezone.utc)
        self._emit("cos.lifecycle.transition", entity, extra={"from": old.value, "to": new_state.value, "reason": reason})
        return entity

    def get(self, entity_id: str) -> Optional[ManagedEntity]:
        with self._lock:
            return self._entities.get(entity_id)

    def list_by_kind(self, kind: str) -> list[ManagedEntity]:
        with self._lock:
            return [e for e in self._entities.values() if e.kind == kind]

    def _emit(self, event_type: str, entity: ManagedEntity, extra: dict | None = None) -> None:
        if not self.ledger:
            return
        payload = {"entity_id": entity.entity_id, "kind": entity.kind, "name": entity.name, "state": entity.state.value}
        if extra:
            payload.update(extra)
        self.ledger.append(EventEnvelope(event_type=event_type, producer_id="cos.lifecycle", payload=payload))
