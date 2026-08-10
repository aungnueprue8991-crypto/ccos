"""COG Knowledge Graph — entities, relations, facts with provenance."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from constitution.schemas.event import EpistemicStatus, EventEnvelope
from kernel.events.ledger import EventLedger


class Entity(BaseModel):
    entity_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    entity_type: str = "concept"
    properties: dict = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Relation(BaseModel):
    relation_id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    relation_type: str
    properties: dict = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    epistemic_status: EpistemicStatus = EpistemicStatus.UNVERIFIED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeGraph:
    def __init__(self, ledger: Optional[EventLedger] = None, db_path: Path | str = "storage/knowledge.db"):
        self.ledger = ledger
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init()

    def _init(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY, name TEXT NOT NULL, entity_type TEXT,
                    properties TEXT, provenance TEXT, created_at TEXT, raw_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS relations (
                    relation_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL, properties TEXT, provenance TEXT,
                    confidence REAL, epistemic_status TEXT, created_at TEXT, raw_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_rel_src ON relations(source_id);
                CREATE INDEX IF NOT EXISTS idx_rel_tgt ON relations(target_id);
                """
            )
            self._conn.commit()

    def add_entity(self, name: str, entity_type: str = "concept", properties: dict | None = None, provenance: list[str] | None = None) -> Entity:
        e = Entity(name=name, entity_type=entity_type, properties=properties or {}, provenance=provenance or [])
        with self._lock:
            self._conn.execute(
                "INSERT INTO entities VALUES (?,?,?,?,?,?,?)",
                (e.entity_id, e.name, e.entity_type, json.dumps(e.properties), json.dumps(e.provenance), e.created_at.isoformat(), e.model_dump_json()),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(EventEnvelope(event_type="cog.knowledge.entity", producer_id="cog.knowledge", payload={"entity_id": e.entity_id, "name": name}))
        return e

    def add_relation(self, source_id: str, target_id: str, relation_type: str, confidence: float = 0.5, provenance: list[str] | None = None) -> Relation:
        if not provenance:
            raise PermissionError("CCOS-002: relation requires provenance")
        r = Relation(
            source_id=source_id, target_id=target_id, relation_type=relation_type,
            confidence=confidence, provenance=provenance,
            epistemic_status=EpistemicStatus.SUPPORTED if confidence >= 0.7 else EpistemicStatus.UNVERIFIED,
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO relations VALUES (?,?,?,?,?,?,?,?,?,?)",
                (r.relation_id, r.source_id, r.target_id, r.relation_type, json.dumps(r.properties),
                 json.dumps(r.provenance), r.confidence, r.epistemic_status.value, r.created_at.isoformat(), r.model_dump_json()),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="cog.knowledge.relation", producer_id="cog.knowledge",
                payload={"relation_id": r.relation_id, "type": relation_type, "confidence": confidence},
            ))
        return r

    def neighbors(self, entity_id: str) -> List[Relation]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM relations WHERE source_id = ? OR target_id = ?", (entity_id, entity_id))
            return [Relation.model_validate_json(r[0]) for r in cur.fetchall()]

    def find_entity(self, name: str) -> Optional[Entity]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM entities WHERE name = ?", (name,))
            row = cur.fetchone()
            return Entity.model_validate_json(row[0]) if row else None
