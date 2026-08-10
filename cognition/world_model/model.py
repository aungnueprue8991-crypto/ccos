"""COG World Model — state, dynamics, latent variables (skeleton with durable store)."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class WorldState(BaseModel):
    state_id: str = Field(default_factory=lambda: str(uuid4()))
    variables: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: list[str] = Field(default_factory=list)
    parent_state_id: Optional[str] = None


class WorldModel:
    def __init__(self, ledger: Optional[EventLedger] = None, db_path: Path | str = "storage/world_model.db"):
        self.ledger = ledger
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._current: Optional[WorldState] = None
        self._init()

    def _init(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS states (
                    state_id TEXT PRIMARY KEY,
                    variables TEXT NOT NULL,
                    timestamp TEXT,
                    provenance TEXT,
                    parent_state_id TEXT,
                    raw_json TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def snapshot(self, variables: Dict[str, Any], provenance: list[str] | None = None) -> WorldState:
        parent = self._current.state_id if self._current else None
        state = WorldState(variables=variables, provenance=provenance or [], parent_state_id=parent)
        with self._lock:
            self._conn.execute(
                "INSERT INTO states VALUES (?,?,?,?,?,?)",
                (state.state_id, json.dumps(state.variables, default=str), state.timestamp.isoformat(),
                 json.dumps(state.provenance), state.parent_state_id, state.model_dump_json()),
            )
            self._conn.commit()
            self._current = state
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="cog.world_model.snapshot", producer_id="cog.world_model",
                payload={"state_id": state.state_id, "n_vars": len(variables)},
            ))
        return state

    def current(self) -> Optional[WorldState]:
        return self._current

    def get(self, state_id: str) -> Optional[WorldState]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM states WHERE state_id = ?", (state_id,))
            row = cur.fetchone()
            return WorldState.model_validate_json(row[0]) if row else None

    def predict(self, intervention: Dict[str, Any]) -> Dict[str, Any]:
        base = dict(self._current.variables) if self._current else {}
        base.update(intervention)
        base["_predicted"] = True
        return base
