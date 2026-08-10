"""Typed event bus — all inter-subsystem communication flows here."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, DefaultDict, List

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


Handler = Callable[[EventEnvelope], Awaitable[None] | None]


class EventBus:
    """In-process pub/sub with durable ledger backing."""

    def __init__(self, ledger: EventLedger):
        self.ledger = ledger
        self._handlers: DefaultDict[str, List[Handler]] = defaultdict(list)
        self._wildcard: List[Handler] = []

    def subscribe(self, event_type: str, handler: Handler) -> None:
        if event_type == "*":
            self._wildcard.append(handler)
        else:
            self._handlers[event_type].append(handler)

    def publish(self, event: EventEnvelope) -> EventEnvelope:
        """Synchronous publish: persist then dispatch."""
        persisted = self.ledger.append(event)
        for handler in self._handlers.get(event.event_type, []):
            result = handler(persisted)
            if asyncio.iscoroutine(result):
                asyncio.get_event_loop().create_task(result)
        for handler in self._wildcard:
            result = handler(persisted)
            if asyncio.iscoroutine(result):
                asyncio.get_event_loop().create_task(result)
        return persisted

    async def publish_async(self, event: EventEnvelope) -> EventEnvelope:
        persisted = self.ledger.append(event)
        tasks = []
        for handler in self._handlers.get(event.event_type, []) + self._wildcard:
            result = handler(persisted)
            if asyncio.iscoroutine(result):
                tasks.append(result)
        if tasks:
            await asyncio.gather(*tasks)
        return persisted
