"""COG Experience Recorder — execution outcomes linked to intents and evidence."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class Experience(BaseModel):
    experience_id: str = Field(default_factory=lambda: str(uuid4()))
    intent_id: Optional[str] = None
    action: str
    outcome: str
    success: bool
    metrics: dict = Field(default_factory=dict)
    context: dict = Field(default_factory=dict)
    causal_links: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExperienceRecorder:
    def __init__(self, ledger: Optional[EventLedger] = None, db_path: Path | str = "storage/experience.db"):
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
                CREATE TABLE IF NOT EXISTS experiences (
                    experience_id TEXT PRIMARY KEY,
                    intent_id TEXT,
                    action TEXT,
                    outcome TEXT,
                    success INTEGER,
                    metrics TEXT,
                    context TEXT,
                    causal_links TEXT,
                    created_at TEXT,
                    raw_json TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def record(
        self,
        action: str,
        outcome: str,
        success: bool,
        intent_id: Optional[str] = None,
        metrics: dict | None = None,
        context: dict | None = None,
        causal_links: list[str] | None = None,
    ) -> Experience:
        exp = Experience(
            intent_id=intent_id,
            action=action,
            outcome=outcome,
            success=success,
            metrics=metrics or {},
            context=context or {},
            causal_links=causal_links or [],
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO experiences VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    exp.experience_id,
                    exp.intent_id,
                    exp.action,
                    exp.outcome,
                    1 if exp.success else 0,
                    json.dumps(exp.metrics),
                    json.dumps(exp.context),
                    json.dumps(exp.causal_links),
                    exp.created_at.isoformat(),
                    exp.model_dump_json(),
                ),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="cog.experience.recorded",
                    producer_id="cog.experience",
                    payload={
                        "experience_id": exp.experience_id,
                        "action": action,
                        "success": success,
                        "intent_id": intent_id,
                    },
                    correlation_id=intent_id,
                )
            )
        return exp

    def by_intent(self, intent_id: str) -> List[Experience]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT raw_json FROM experiences WHERE intent_id = ?", (intent_id,)
            )
            return [Experience.model_validate_json(r[0]) for r in cur.fetchall()]
