"""AGS → NEXUS HybridMemory bridge — high-confidence items only, with provenance."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ags.shared.database import get_db, jload
from nexus.memory.hybrid import HybridMemory, MemoryEntry


class AGSNexusBridge:
    """Copy selected AGS knowledge/episodes into NEXUS HybridMemory."""

    def __init__(self, agent_id: str, db_path: Optional[str] = None):
        self.agent_id = agent_id
        self.db = get_db(db_path) if db_path else get_db()

    def export_knowledge(
        self,
        memory: HybridMemory,
        min_confidence: float = 0.7,
        verified_only: bool = False,
        limit: int = 50,
    ) -> int:
        sql = (
            "SELECT * FROM knowledge WHERE agent_id=? AND confidence>=? "
            + ("AND verified=1 " if verified_only else "")
            + "ORDER BY confidence DESC LIMIT ?"
        )
        rows = self.db.fetchall(sql, (self.agent_id, min_confidence, limit))
        n = 0
        for r in rows:
            memory.write(
                MemoryEntry(
                    content=r.get("content") or "",
                    domain=r.get("domain") or "ags",
                    tags=jload(r.get("tags"), []) or ["ags_knowledge"],
                    type="semantic",
                    confidence=float(r.get("confidence") or 0.5),
                    provenance=[
                        f"ags:knowledge:{r.get('item_id')}",
                        f"source:{r.get('source') or 'ags'}",
                        "bridge:ags_nexus",
                    ],
                )
            )
            n += 1
        return n

    def export_episodes(
        self,
        memory: HybridMemory,
        min_importance: float = 0.5,
        limit: int = 30,
    ) -> int:
        rows = self.db.fetchall(
            "SELECT * FROM episodes WHERE agent_id=? AND importance>=? "
            "ORDER BY importance DESC, created_at DESC LIMIT ?",
            (self.agent_id, min_importance, limit),
        )
        n = 0
        for r in rows:
            memory.write(
                MemoryEntry(
                    content=r.get("description") or "",
                    domain="episodic",
                    tags=jload(r.get("tags"), []) or ["ags_episode"],
                    type="episodic",
                    confidence=float(r.get("importance") or 0.5),
                    provenance=[
                        f"ags:episode:{r.get('episode_id')}",
                        "bridge:ags_nexus",
                    ],
                )
            )
            n += 1
        return n
