"""COG Belief Store — confidence, support, contradiction, revision."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from constitution.schemas.event import EpistemicStatus, EventEnvelope
from kernel.events.ledger import EventLedger


class Belief(BaseModel):
    belief_id: str = Field(default_factory=lambda: str(uuid4()))
    proposition: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    support: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    epistemic_status: EpistemicStatus = EpistemicStatus.UNVERIFIED
    source_evidence: list[str] = Field(default_factory=list)
    revised_from: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BeliefStore:
    def __init__(self, ledger: Optional[EventLedger] = None, db_path: Path | str = "storage/beliefs.db"):
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
                CREATE TABLE IF NOT EXISTS beliefs (
                    belief_id TEXT PRIMARY KEY, proposition TEXT NOT NULL, confidence REAL,
                    support TEXT, contradictions TEXT, epistemic_status TEXT,
                    source_evidence TEXT, revised_from TEXT, created_at TEXT, raw_json TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def assert_belief(self, proposition: str, evidence_ids: list[str], confidence: float = 0.5) -> Belief:
        if not evidence_ids:
            raise PermissionError("CCOS-002: belief requires provenance (evidence)")
        b = Belief(
            proposition=proposition, confidence=confidence, source_evidence=evidence_ids,
            support=evidence_ids,
            epistemic_status=EpistemicStatus.SUPPORTED if confidence >= 0.7 else EpistemicStatus.UNVERIFIED,
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO beliefs VALUES (?,?,?,?,?,?,?,?,?,?)",
                (b.belief_id, b.proposition, b.confidence, json.dumps(b.support), json.dumps(b.contradictions),
                 b.epistemic_status.value, json.dumps(b.source_evidence), b.revised_from,
                 b.created_at.isoformat(), b.model_dump_json()),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="cog.belief.asserted", producer_id="cog.beliefs",
                payload={"belief_id": b.belief_id, "proposition": proposition, "confidence": confidence},
            ))
        return b

    def revise(self, belief_id: str, new_confidence: float, reason: str = "") -> Belief:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM beliefs WHERE belief_id = ?", (belief_id,))
            row = cur.fetchone()
            if not row:
                raise KeyError(belief_id)
            old = Belief.model_validate_json(row[0])
        new = Belief(
            proposition=old.proposition, confidence=new_confidence, support=old.support,
            contradictions=old.contradictions, source_evidence=old.source_evidence,
            revised_from=old.belief_id,
            epistemic_status=EpistemicStatus.SUPPORTED if new_confidence >= 0.7 else EpistemicStatus.CONFLICTED,
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO beliefs VALUES (?,?,?,?,?,?,?,?,?,?)",
                (new.belief_id, new.proposition, new.confidence, json.dumps(new.support),
                 json.dumps(new.contradictions), new.epistemic_status.value, json.dumps(new.source_evidence),
                 new.revised_from, new.created_at.isoformat(), new.model_dump_json()),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="cog.belief.revised", producer_id="cog.beliefs",
                payload={"from": belief_id, "to": new.belief_id, "confidence": new_confidence, "reason": reason},
            ))
        return new

    def list_active(self) -> List[Belief]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM beliefs ORDER BY created_at DESC")
            return [Belief.model_validate_json(r[0]) for r in cur.fetchall()]
