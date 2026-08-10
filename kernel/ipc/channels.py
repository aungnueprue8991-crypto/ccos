"""COS IPC — typed, isolated message channels."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class Message:
    message_id: str = field(default_factory=lambda: str(uuid4()))
    channel: str = ""
    sender: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None


class Channel:
    def __init__(self, name: str, maxsize: int = 1000):
        self.name = name
        self._q: queue.Queue[Message] = queue.Queue(maxsize=maxsize)

    def send(self, msg: Message) -> None:
        msg.channel = self.name
        self._q.put(msg, block=True, timeout=5)

    def receive(self, timeout: float = 1.0) -> Optional[Message]:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None


class IPC:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._channels: Dict[str, Channel] = {}
        self._lock = threading.RLock()

    def create_channel(self, name: str) -> Channel:
        with self._lock:
            if name not in self._channels:
                self._channels[name] = Channel(name)
                if self.ledger:
                    self.ledger.append(
                        EventEnvelope(
                            event_type="cos.ipc.channel_created",
                            producer_id="cos.ipc",
                            payload={"channel": name},
                        )
                    )
            return self._channels[name]

    def send(self, channel: str, sender: str, payload: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
        ch = self.create_channel(channel)
        msg = Message(sender=sender, payload=payload, correlation_id=correlation_id)
        ch.send(msg)
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="cos.ipc.send",
                    producer_id="cos.ipc",
                    payload={"channel": channel, "sender": sender, "message_id": msg.message_id},
                    correlation_id=correlation_id,
                )
            )
        return msg.message_id

    def receive(self, channel: str, timeout: float = 1.0) -> Optional[Message]:
        with self._lock:
            ch = self._channels.get(channel)
        if not ch:
            return None
        return ch.receive(timeout=timeout)
