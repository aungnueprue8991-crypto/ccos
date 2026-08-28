"""Production-grade append-only, hash-chained event ledger.

Implements CCOS-006, CCOS-007, CCOS-012.
SQLite for durability + JSONL mirror for human readability.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Iterator, Optional

from constitution.schemas.event import EventEnvelope


def _canonical_hash(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class EventLedger:
    """Thread-safe, durable, hash-chained event ledger."""

    def __init__(self, path: Path | str = "observatory/ledger/events.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.path.with_suffix(".jsonl")
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()
        self._sequence = self._load_sequence()
        self._last_hash = self._load_last_hash()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    producer_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    correlation_id TEXT,
                    causation_id TEXT,
                    payload TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    previous_event_hash TEXT,
                    provenance TEXT,
                    signature TEXT,
                    raw_json TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_producer ON events(producer_id)"
            )
            self._conn.commit()

    def _load_sequence(self) -> int:
        cur = self._conn.execute("SELECT COALESCE(MAX(sequence), -1) FROM events")
        row = cur.fetchone()
        return (row[0] + 1) if row else 0

    def _load_last_hash(self) -> Optional[str]:
        cur = self._conn.execute(
            "SELECT payload_hash FROM events ORDER BY sequence DESC LIMIT 1"
        )
        row = cur.fetchone()
        return row[0] if row else None

    def append(self, event: EventEnvelope) -> EventEnvelope:
        with self._lock:
            event.sequence = self._sequence
            event.previous_event_hash = self._last_hash
            data = event.model_dump(mode="json")
            data.pop("signature", None)
            data.pop("payload_hash", None)
            event.payload_hash = _canonical_hash(data)
            self._last_hash = event.payload_hash
            raw = event.model_dump_json()

            self._conn.execute(
                """
                INSERT INTO events (
                    sequence, event_id, event_type, producer_id, timestamp,
                    correlation_id, causation_id, payload, payload_hash,
                    previous_event_hash, provenance, signature, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.sequence,
                    event.event_id,
                    event.event_type,
                    event.producer_id,
                    event.timestamp.isoformat(),
                    event.correlation_id,
                    event.causation_id,
                    json.dumps(event.payload, default=str),
                    event.payload_hash,
                    event.previous_event_hash,
                    json.dumps(event.provenance),
                    event.signature,
                    raw,
                ),
            )
            self._conn.commit()
            self._sequence += 1

            try:
                with self.jsonl_path.open("a", encoding="utf-8") as f:
                    f.write(raw + "\n")
            except OSError:
                pass
            return event

    def iter_events(self) -> Iterator[EventEnvelope]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM events ORDER BY sequence ASC")
            rows = cur.fetchall()
        for (raw,) in rows:
            yield EventEnvelope.model_validate_json(raw)

    def get_by_id(self, event_id: str) -> Optional[EventEnvelope]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT raw_json FROM events WHERE event_id = ?", (event_id,)
            )
            row = cur.fetchone()
            return EventEnvelope.model_validate_json(row[0]) if row else None

    def find_by_type(self, event_type: str) -> list[EventEnvelope]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT raw_json FROM events WHERE event_type = ? ORDER BY sequence",
                (event_type,),
            )
            return [EventEnvelope.model_validate_json(r[0]) for r in cur.fetchall()]

    def verify_chain(self) -> bool:
        prev_hash: Optional[str] = None
        for ev in self.iter_events():
            data = ev.model_dump(mode="json")
            data.pop("signature", None)
            data.pop("payload_hash", None)
            expected = _canonical_hash(data)
            if ev.payload_hash != expected:
                return False
            if prev_hash is not None and ev.previous_event_hash != prev_hash:
                return False
            prev_hash = ev.payload_hash
        return True

    def count(self) -> int:
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(*) FROM events")
            return cur.fetchone()[0]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
