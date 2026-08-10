"""Production COG Evidence Pipeline with full epistemic status machine."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional

from constitution.schemas.event import Evidence, EpistemicStatus, EventEnvelope
from kernel.events.ledger import EventLedger


class EvidencePipeline:
    def __init__(
        self,
        ledger: Optional[EventLedger] = None,
        db_path: Path | str = "storage/evidence.db",
    ):
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
                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id TEXT PRIMARY KEY,
                    claim TEXT NOT NULL,
                    source TEXT NOT NULL,
                    observation_refs TEXT,
                    provenance TEXT,
                    timestamp TEXT,
                    methodology TEXT,
                    confidence REAL,
                    independent_support TEXT,
                    contradictions TEXT,
                    verification_state TEXT,
                    epistemic_status TEXT,
                    raw_json TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def _persist(self, ev: Evidence) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO evidence
                (evidence_id, claim, source, observation_refs, provenance, timestamp,
                 methodology, confidence, independent_support, contradictions,
                 verification_state, epistemic_status, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ev.evidence_id, ev.claim, ev.source,
                    json.dumps(ev.observation_refs), json.dumps(ev.provenance),
                    ev.timestamp.isoformat(), ev.methodology, ev.confidence,
                    json.dumps(ev.independent_support), json.dumps(ev.contradictions),
                    ev.verification_state.value, ev.epistemic_status.value,
                    ev.model_dump_json(),
                ),
            )
            self._conn.commit()

    def ingest_observation(
        self, claim: str, source: str,
        observation_refs: list[str] | None = None,
        provenance: list[str] | None = None,
    ) -> Evidence:
        ev = Evidence(
            claim=claim, source=source,
            observation_refs=observation_refs or [],
            provenance=provenance or [],
            epistemic_status=EpistemicStatus.UNVERIFIED,
            verification_state=EpistemicStatus.UNVERIFIED,
        )
        self._persist(ev)
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="cog.observation", producer_id="cog.evidence",
                payload={"evidence_id": ev.evidence_id, "claim": claim, "source": source},
            ))
        return ev

    def validate(self, evidence_id: str, confidence: float, methodology: str = "") -> Evidence:
        ev = self.get(evidence_id)
        if ev is None:
            raise KeyError(evidence_id)
        ev.confidence = max(0.0, min(1.0, confidence))
        ev.methodology = methodology
        ev.verification_state = EpistemicStatus.VALIDATING
        if ev.confidence >= 0.7:
            ev.epistemic_status = EpistemicStatus.SUPPORTED
            ev.verification_state = EpistemicStatus.SUPPORTED
        elif ev.confidence < 0.3:
            ev.epistemic_status = EpistemicStatus.REJECTED
            ev.verification_state = EpistemicStatus.REJECTED
        self._persist(ev)
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="cog.evidence.validated", producer_id="cog.evidence",
                payload={"evidence_id": evidence_id, "status": ev.epistemic_status.value, "confidence": ev.confidence},
            ))
        return ev

    def corroborate(self, evidence_id: str, support_refs: list[str]) -> Evidence:
        ev = self.get(evidence_id)
        if ev is None:
            raise KeyError(evidence_id)
        ev.independent_support = list(set(ev.independent_support + support_refs))
        if len(ev.independent_support) >= 2 and ev.epistemic_status == EpistemicStatus.SUPPORTED:
            ev.epistemic_status = EpistemicStatus.CORROBORATED
            ev.verification_state = EpistemicStatus.CORROBORATED
        self._persist(ev)
        return ev

    def get(self, evidence_id: str) -> Optional[Evidence]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM evidence WHERE evidence_id = ?", (evidence_id,))
            row = cur.fetchone()
            return Evidence.model_validate_json(row[0]) if row else None

    def list_by_status(self, status: EpistemicStatus) -> List[Evidence]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM evidence WHERE epistemic_status = ?", (status.value,))
            return [Evidence.model_validate_json(r[0]) for r in cur.fetchall()]
