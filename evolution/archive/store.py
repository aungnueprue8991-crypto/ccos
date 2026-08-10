"""Durable experiment archive — params, seeds, public/private scores, artifacts."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class ArchivedRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    experiment_id: str = ""
    hypothesis_ref: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    random_seed: int = 42
    public_metrics: Dict[str, float] = Field(default_factory=dict)
    private_metrics: Dict[str, float] = Field(default_factory=dict)
    code_hash: str = ""
    reproducible: bool = True
    artifacts: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExperimentArchive:
    def __init__(self, ledger: Optional[EventLedger] = None, db_path: Path | str = "storage/experiments.db"):
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
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY, experiment_id TEXT, hypothesis_ref TEXT,
                    parameters TEXT, random_seed INTEGER, public_metrics TEXT,
                    private_metrics TEXT, code_hash TEXT, reproducible INTEGER,
                    artifacts TEXT, created_at TEXT, raw_json TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def archive(self, experiment_id: str, parameters: dict, public_metrics: dict[str, float],
                private_metrics: dict[str, float] | None = None, random_seed: int = 42,
                hypothesis_ref: str | None = None, code_hash: str = "",
                artifacts: list[str] | None = None) -> ArchivedRun:
        run = ArchivedRun(
            experiment_id=experiment_id, hypothesis_ref=hypothesis_ref, parameters=parameters,
            random_seed=random_seed, public_metrics=public_metrics,
            private_metrics=private_metrics or {}, code_hash=code_hash, artifacts=artifacts or [],
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (run.run_id, run.experiment_id, run.hypothesis_ref, json.dumps(run.parameters),
                 run.random_seed, json.dumps(run.public_metrics), json.dumps(run.private_metrics),
                 run.code_hash, 1 if run.reproducible else 0, json.dumps(run.artifacts),
                 run.created_at.isoformat(), run.model_dump_json()),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="scos.experiment.archived", producer_id="scos.archive",
                payload={"run_id": run.run_id, "experiment_id": experiment_id,
                         "public_metrics": public_metrics, "has_private": bool(private_metrics),
                         "seed": random_seed},
            ))
        return run

    def get(self, run_id: str) -> Optional[ArchivedRun]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM runs WHERE run_id = ?", (run_id,))
            row = cur.fetchone()
            return ArchivedRun.model_validate_json(row[0]) if row else None

    def list_by_hypothesis(self, hypothesis_ref: str) -> List[ArchivedRun]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM runs WHERE hypothesis_ref = ?", (hypothesis_ref,))
            return [ArchivedRun.model_validate_json(r[0]) for r in cur.fetchall()]

    def count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
