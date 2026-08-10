"""Production Observatory — answers 'What happened?' with integrity guarantees."""

from __future__ import annotations

from typing import Iterator

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class Observatory:
    def __init__(self, ledger: EventLedger):
        self.ledger = ledger

    def record(self, event: EventEnvelope) -> EventEnvelope:
        return self.ledger.append(event)

    def replay(self) -> Iterator[EventEnvelope]:
        yield from self.ledger.iter_events()

    def verify_integrity(self) -> bool:
        return self.ledger.verify_chain()

    def find_by_type(self, event_type: str) -> list[EventEnvelope]:
        return self.ledger.find_by_type(event_type)

    def reconstruction_summary(self) -> dict:
        events = list(self.replay())
        types: dict[str, int] = {}
        for e in events:
            types[e.event_type] = types.get(e.event_type, 0) + 1
        return {
            "total_events": len(events),
            "by_type": types,
            "chain_valid": self.verify_integrity(),
            "last_sequence": events[-1].sequence if events else None,
            "db_count": self.ledger.count(),
        }
