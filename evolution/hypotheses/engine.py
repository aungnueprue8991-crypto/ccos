"""SCOS Hypothesis Engine — generation, ranking, falsification tracking."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional

from constitution.schemas.scos import Hypothesis, HypothesisStatus
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class HypothesisEngine:
    def __init__(self, ledger: Optional[EventLedger] = None, db_path: Path | str = "storage/hypotheses.db"):
        self.ledger = ledger
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init()

    def _init(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hypotheses (
                    hypothesis_id TEXT PRIMARY KEY, statement TEXT NOT NULL, predictions TEXT,
                    domain TEXT, status TEXT, provenance TEXT, confidence REAL,
                    created_at TEXT, raw_json TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def generate(self, statement: str, predictions: list[str] | None = None, domain: str = "general", provenance: list[str] | None = None) -> Hypothesis:
        h = Hypothesis(statement=statement, predictions=predictions or [], domain=domain, provenance=provenance or [], status=HypothesisStatus.GENERATED)
        self._persist(h)
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="scos.hypothesis.generated", producer_id="scos.hypotheses",
                payload={"hypothesis_id": h.hypothesis_id, "statement": statement, "domain": domain},
            ))
        return h

    def rank(self, hypothesis_id: str, confidence: float) -> Hypothesis:
        h = self.get(hypothesis_id)
        if not h:
            raise KeyError(hypothesis_id)
        h.confidence = max(0.0, min(1.0, confidence))
        h.status = HypothesisStatus.RANKED
        self._persist(h)
        return h

    def falsify(self, hypothesis_id: str, reason: str = "") -> Hypothesis:
        h = self.get(hypothesis_id)
        if not h:
            raise KeyError(hypothesis_id)
        h.status = HypothesisStatus.FALSIFIED
        self._persist(h)
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="scos.hypothesis.falsified", producer_id="scos.hypotheses",
                payload={"hypothesis_id": hypothesis_id, "reason": reason},
            ))
        return h

    def support(self, hypothesis_id: str) -> Hypothesis:
        h = self.get(hypothesis_id)
        if not h:
            raise KeyError(hypothesis_id)
        h.status = HypothesisStatus.SUPPORTED
        self._persist(h)
        return h

    def get(self, hypothesis_id: str) -> Optional[Hypothesis]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM hypotheses WHERE hypothesis_id = ?", (hypothesis_id,))
            row = cur.fetchone()
            return Hypothesis.model_validate_json(row[0]) if row else None

    def list_by_status(self, status: HypothesisStatus) -> List[Hypothesis]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM hypotheses WHERE status = ?", (status.value,))
            return [Hypothesis.model_validate_json(r[0]) for r in cur.fetchall()]

    def _persist(self, h: Hypothesis) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO hypotheses VALUES (?,?,?,?,?,?,?,?,?)",
                (h.hypothesis_id, h.statement, json.dumps(h.predictions), h.domain,
                 h.status.value, json.dumps(h.provenance), h.confidence,
                 h.created_at.isoformat(), h.model_dump_json()),
            )
            self._conn.commit()
