"""Bridge NEXUS cognitive events onto the CCOS EventLedger (hash-chained)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class NexusLedgerBridge:
    """Every NEXUS emit becomes a durable, hash-chained EventEnvelope."""

    PRODUCER = "nexus.orchestrator"

    def __init__(self, path: Path | str | None = None):
        if path is None:
            path = Path("observatory/ledger/nexus_events.db")
        self.ledger = EventLedger(path)
        self.correlation_id: Optional[str] = None
        self._last_event_id: Optional[str] = None

    def set_correlation(self, correlation_id: str) -> None:
        self.correlation_id = correlation_id

    def emit(self, event_type: str, payload: Dict[str, Any]) -> EventEnvelope:
        et = event_type if event_type.startswith("nexus.") else f"nexus.{event_type}"
        safe = _json_safe(payload)
        env = EventEnvelope(
            event_type=et,
            producer_id=self.PRODUCER,
            payload=safe,
            correlation_id=self.correlation_id,
            causation_id=self._last_event_id,
            provenance=["nexus", "cognitive_cycle"],
        )
        stored = self.ledger.append(env)
        self._last_event_id = stored.event_id
        return stored

    def count(self) -> int:
        return self.ledger.count()

    def verify_chain(self) -> bool:
        return self.ledger.verify_chain()

    def close(self) -> None:
        self.ledger.close()


def _json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    if hasattr(obj, "value"):
        return obj.value
    return str(obj)
