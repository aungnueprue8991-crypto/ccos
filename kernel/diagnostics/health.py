"""COS health diagnostics."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class HealthReport:
    status: str = "healthy"
    checks: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)


class Diagnostics:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger

    def health(self) -> HealthReport:
        checks: Dict[str, Any] = {}
        if self.ledger:
            checks["chain_valid"] = self.ledger.verify_chain()
            checks["event_count"] = self.ledger.count()
            status = "healthy" if checks["chain_valid"] else "degraded"
        else:
            status = "unknown"
        report = HealthReport(status=status, checks=checks)
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="cos.diagnostics.health",
                    producer_id="cos.diagnostics",
                    payload={"status": status, "checks": checks},
                )
            )
        return report
