"""SCOS / Capability Rollback — lineage-aware reversion."""

from __future__ import annotations
from typing import Optional
from constitution.schemas.capability import CapabilityLifecycle
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger
from kernel.registry.capability_registry import CapabilityRegistry


class RollbackManager:
    def __init__(self, registry: CapabilityRegistry, ledger: Optional[EventLedger] = None):
        self.registry = registry
        self.ledger = ledger
        self._lineage: dict[str, list[str]] = {}

    def record_lineage(self, capability_id: str, previous_id: Optional[str] = None) -> None:
        if capability_id not in self._lineage:
            self._lineage[capability_id] = []
        if previous_id:
            self._lineage[capability_id].append(previous_id)

    def rollback(self, capability_id: str, authorized_by: str, reason: str = "incident") -> str:
        lineage = self._lineage.get(capability_id, [])
        if not lineage:
            self.registry.transition(capability_id, CapabilityLifecycle.REVOKED, reason=reason, authorized_by=authorized_by)
            if self.ledger:
                self.ledger.append(EventEnvelope(
                    event_type="scos.rollback.revoked", producer_id="scos.rollback",
                    payload={"capability_id": capability_id, "reason": reason},
                ))
            return capability_id
        previous = lineage[-1]
        self.registry.transition(capability_id, CapabilityLifecycle.DEPRECATED, reason=reason, authorized_by=authorized_by)
        prev_cap = self.registry.get(previous)
        if prev_cap is None:
            raise KeyError(f"Previous capability {previous} not found")
        if prev_cap.lifecycle_status != CapabilityLifecycle.ACTIVE:
            if prev_cap.lifecycle_status not in (CapabilityLifecycle.APPROVED, CapabilityLifecycle.VERIFIED, CapabilityLifecycle.ACTIVE):
                self.registry.transition(previous, CapabilityLifecycle.APPROVED, reason="rollback restore", authorized_by=authorized_by)
            self.registry.transition(previous, CapabilityLifecycle.ACTIVE, reason="rollback restore", authorized_by=authorized_by)
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="scos.rollback.completed", producer_id="scos.rollback",
                payload={"from": capability_id, "to": previous, "reason": reason, "authorized_by": authorized_by},
            ))
        return previous
