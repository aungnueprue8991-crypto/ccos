"""COS resource manager — CPU/memory quotas."""

from __future__ import annotations
from typing import Dict, Optional
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class ResourceManager:
    def __init__(self, total_cpu: float = 100.0, total_memory_mb: float = 8192.0, ledger: Optional[EventLedger] = None):
        self.total_cpu = total_cpu
        self.total_memory_mb = total_memory_mb
        self.used_cpu = 0.0
        self.used_memory = 0.0
        self.ledger = ledger
        self._allocs: Dict[str, dict] = {}

    def allocate(self, owner: str, cpu: float = 0.0, memory_mb: float = 0.0) -> bool:
        if self.used_cpu + cpu > self.total_cpu or self.used_memory + memory_mb > self.total_memory_mb:
            if self.ledger:
                self.ledger.append(EventEnvelope(
                    event_type="cos.resource.denied",
                    producer_id="cos.resources",
                    payload={"owner": owner, "cpu": cpu, "memory_mb": memory_mb},
                ))
            return False
        self.used_cpu += cpu
        self.used_memory += memory_mb
        self._allocs[owner] = self._allocs.get(owner, {"cpu": 0.0, "memory_mb": 0.0})
        self._allocs[owner]["cpu"] += cpu
        self._allocs[owner]["memory_mb"] += memory_mb
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="cos.resource.allocated",
                producer_id="cos.resources",
                payload={"owner": owner, "cpu": cpu, "memory_mb": memory_mb},
            ))
        return True

    def release(self, owner: str) -> None:
        a = self._allocs.pop(owner, None)
        if a:
            self.used_cpu -= a["cpu"]
            self.used_memory -= a["memory_mb"]
