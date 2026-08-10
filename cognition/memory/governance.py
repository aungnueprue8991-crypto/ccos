"""Production Memory Governance — every write is policy-checked and provenance-gated."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional

from constitution.schemas.memory import MemoryRecord, MemoryKind
from constitution.schemas.event import EpistemicStatus, EventEnvelope
from kernel.events.ledger import EventLedger


class MemoryGovernance:
    def __init__(self, ledger: Optional[EventLedger] = None, db_path: Path | str = "storage/memory.db"):
        self.ledger = ledger
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    record_id TEXT PRIMARY KEY, namespace TEXT NOT NULL, kind TEXT NOT NULL,
                    content TEXT NOT NULL, provenance TEXT NOT NULL, epistemic_status TEXT NOT NULL,
                    access_policy TEXT, retention TEXT, writer TEXT, created_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_ns ON memory(namespace)")
            self._conn.commit()

    def write(self, record: MemoryRecord) -> MemoryRecord:
        if not record.provenance:
            raise PermissionError("CCOS-002: no permanent knowledge without provenance")
        if record.epistemic_status == EpistemicStatus.UNVERIFIED and record.kind != MemoryKind.WORKING:
            raise PermissionError("CCOS-003: cannot write unverified claims to non-working memory")
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO memory
                (record_id, namespace, kind, content, provenance, epistemic_status,
                 access_policy, retention, writer, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (record.record_id, record.namespace, record.kind.value,
                 json.dumps(record.content, default=str), json.dumps(record.provenance),
                 record.epistemic_status.value, json.dumps(record.access_policy),
                 record.retention, record.writer, record.created_at.isoformat()),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="memory.write", producer_id="cog.memory",
                payload={
                    "record_id": record.record_id, "namespace": record.namespace,
                    "kind": record.kind.value, "epistemic_status": record.epistemic_status.value,
                    "writer": record.writer,
                },
                provenance=record.provenance,
            ))
        return record

    def query(self, namespace: str, kind: Optional[MemoryKind] = None, min_status: Optional[EpistemicStatus] = None) -> List[MemoryRecord]:
        with self._lock:
            sql = "SELECT * FROM memory WHERE namespace = ?"
            params: list = [namespace]
            if kind:
                sql += " AND kind = ?"
                params.append(kind.value)
            cur = self._conn.execute(sql, params)
            rows = cur.fetchall()
        results = []
        for row in rows:
            rec = MemoryRecord(
                record_id=row[0], namespace=row[1], kind=MemoryKind(row[2]),
                content=json.loads(row[3]), provenance=json.loads(row[4]),
                epistemic_status=EpistemicStatus(row[5]),
                access_policy=json.loads(row[6] or "[]"),
                retention=row[7] or "permanent", writer=row[8] or "",
            )
            if min_status:
                order = list(EpistemicStatus)
                if order.index(rec.epistemic_status) < order.index(min_status):
                    continue
            results.append(rec)
        return results
