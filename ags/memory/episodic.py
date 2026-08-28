"""Episodic memory — what happened, when, outcome, valence."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ags.shared.database import get_db, jdump, jload
from ags.shared.types import EpisodicMemory, new_id, now_ts


class EpisodicStore:
    def __init__(self, agent_id: str, capacity: int = 1000, db_path: Optional[str] = None):
        self.agent_id = agent_id
        self.capacity = capacity
        self.db = get_db(db_path) if db_path else get_db()

    def record(
        self,
        description: str,
        context: Optional[Dict] = None,
        outcome: str = "",
        valence: float = 0.0,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        goal_id: Optional[str] = None,
    ) -> str:
        ep_id = new_id()
        ctx = dict(context or {})
        if goal_id:
            ctx["goal_id"] = goal_id
        with self.db.tx() as conn:
            conn.execute(
                """INSERT INTO episodes
                   (episode_id, agent_id, description, context, outcome,
                    valence, importance, tags, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ep_id,
                    self.agent_id,
                    description,
                    jdump(ctx),
                    outcome,
                    valence,
                    importance,
                    jdump(tags or []),
                    now_ts(),
                ),
            )
        self._enforce_capacity()
        return ep_id

    def get_recent(self, limit: int = 20) -> List[EpisodicMemory]:
        rows = self.db.fetchall(
            "SELECT * FROM episodes WHERE agent_id=? ORDER BY created_at DESC LIMIT ?",
            (self.agent_id, limit),
        )
        return [self._row_to_ep(r) for r in rows]

    def get_important(self, threshold: float = 0.7, limit: int = 20) -> List[EpisodicMemory]:
        rows = self.db.fetchall(
            "SELECT * FROM episodes WHERE agent_id=? AND importance>=? "
            "ORDER BY importance DESC, created_at DESC LIMIT ?",
            (self.agent_id, threshold, limit),
        )
        return [self._row_to_ep(r) for r in rows]

    def search(self, keyword: str, limit: int = 10) -> List[EpisodicMemory]:
        rows = self.db.fetchall(
            "SELECT * FROM episodes WHERE agent_id=? AND (description LIKE ? OR outcome LIKE ?) "
            "ORDER BY importance DESC LIMIT ?",
            (self.agent_id, f"%{keyword}%", f"%{keyword}%", limit),
        )
        return [self._row_to_ep(r) for r in rows]

    def get_context_for_llm(self, limit: int = 5) -> str:
        episodes = self.get_recent(limit)
        if not episodes:
            return "No prior experiences recorded."
        lines = ["Recent experiences:"]
        for ep in episodes:
            mark = "✓" if ep.emotional_valence > 0 else ("✗" if ep.emotional_valence < -0.1 else "~")
            lines.append(f"  [{mark}] {ep.description[:100]}")
            if ep.outcome:
                lines.append(f"      → {ep.outcome[:80]}")
        return "\n".join(lines)

    def count(self) -> int:
        row = self.db.fetchone(
            "SELECT COUNT(*) as c FROM episodes WHERE agent_id=?", (self.agent_id,)
        )
        return int(row["c"]) if row else 0

    def _enforce_capacity(self) -> None:
        n = self.count()
        if n <= self.capacity:
            return
        excess = n - self.capacity
        with self.db.tx() as conn:
            conn.execute(
                """DELETE FROM episodes WHERE episode_id IN (
                     SELECT episode_id FROM episodes WHERE agent_id=?
                     ORDER BY importance ASC, created_at ASC LIMIT ?)""",
                (self.agent_id, excess),
            )

    def _row_to_ep(self, row: Dict) -> EpisodicMemory:
        return EpisodicMemory(
            episode_id=row["episode_id"],
            agent_id=row["agent_id"],
            description=row["description"],
            context=jload(row.get("context"), {}),
            outcome=row.get("outcome") or "",
            emotional_valence=row.get("valence") or 0.0,
            importance=row.get("importance") or 0.5,
            tags=jload(row.get("tags"), []),
            timestamp=row.get("created_at") or 0.0,
        )
