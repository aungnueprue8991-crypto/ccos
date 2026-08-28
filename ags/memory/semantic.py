"""Semantic memory — knowledge with confidence, provenance, decay."""

from __future__ import annotations

from typing import Dict, List, Optional

from ags.shared.database import get_db, jdump, jload
from ags.shared.types import KnowledgeItem, new_id, now_ts

DECAY_THRESHOLD = 0.1
MIN_CONFIDENCE = 0.01
MAX_CONFIDENCE = 0.99


class SemanticMemory:
    def __init__(self, agent_id: str, db_path: Optional[str] = None):
        self.agent_id = agent_id
        self.db = get_db(db_path) if db_path else get_db()

    def store(
        self,
        content: str,
        domain: str = "general",
        confidence: float = 0.5,
        source: str = "observation",
        source_type: str = "observation",
        evidence: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        existing = self._find_similar(content, domain)
        if existing:
            return self._update_confidence(existing["item_id"], confidence, evidence or [])
        item_id = new_id()
        with self.db.tx() as conn:
            conn.execute(
                """INSERT INTO knowledge
                   (item_id, agent_id, content, domain, confidence, evidence,
                    source, source_type, verified, tags, access_count, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 0, ?, ?)""",
                (
                    item_id,
                    self.agent_id,
                    content,
                    domain,
                    confidence,
                    jdump(evidence or []),
                    source,
                    source_type,
                    jdump(tags or []),
                    now_ts(),
                    now_ts(),
                ),
            )
        return item_id

    def _update_confidence(self, item_id: str, strength: float, evidence: List[str]) -> str:
        existing = self.db.fetchone(
            "SELECT confidence, evidence FROM knowledge WHERE item_id=?", (item_id,)
        )
        if not existing:
            return item_id
        old = existing["confidence"]
        new_conf = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, old + 0.3 * (strength - old)))
        updated = list(set(jload(existing["evidence"], []) + evidence))
        with self.db.tx() as conn:
            conn.execute(
                "UPDATE knowledge SET confidence=?, evidence=?, updated_at=? WHERE item_id=?",
                (new_conf, jdump(updated), now_ts(), item_id),
            )
        return item_id

    def retrieve(
        self, domain: Optional[str] = None, min_confidence: float = 0.0, limit: int = 20
    ) -> List[KnowledgeItem]:
        sql = "SELECT * FROM knowledge WHERE agent_id=? AND confidence>=?"
        params: list = [self.agent_id, min_confidence]
        if domain:
            sql += " AND domain=?"
            params.append(domain)
        sql += " ORDER BY confidence DESC, access_count DESC LIMIT ?"
        params.append(limit)
        rows = self.db.fetchall(sql, tuple(params))
        ids = [r["item_id"] for r in rows]
        if ids:
            with self.db.tx() as conn:
                conn.execute(
                    f"UPDATE knowledge SET access_count=access_count+1 WHERE item_id IN ({','.join('?'*len(ids))})",
                    ids,
                )
        return [self._row_to_item(r) for r in rows]

    def search(
        self, keyword: str, domain: Optional[str] = None, limit: int = 10
    ) -> List[KnowledgeItem]:
        params: list = [self.agent_id, f"%{keyword}%"]
        sql = "SELECT * FROM knowledge WHERE agent_id=? AND content LIKE ?"
        if domain:
            sql += " AND domain=?"
            params.append(domain)
        sql += " ORDER BY confidence DESC LIMIT ?"
        params.append(limit)
        return [self._row_to_item(r) for r in self.db.fetchall(sql, tuple(params))]

    def get_uncertain(
        self, domain: Optional[str] = None, limit: int = 10
    ) -> List[KnowledgeItem]:
        params: list = [self.agent_id, 0.2, 0.7]
        sql = "SELECT * FROM knowledge WHERE agent_id=? AND confidence>=? AND confidence<=?"
        if domain:
            sql += " AND domain=?"
            params.append(domain)
        sql += " ORDER BY confidence ASC LIMIT ?"
        params.append(limit)
        return [self._row_to_item(r) for r in self.db.fetchall(sql, tuple(params))]

    def verify(self, item_id: str, verified: bool = True) -> None:
        with self.db.tx() as conn:
            if verified:
                conn.execute(
                    "UPDATE knowledge SET verified=1, confidence=MIN(0.95, confidence+0.2), updated_at=? WHERE item_id=?",
                    (now_ts(), item_id),
                )
            else:
                conn.execute(
                    "UPDATE knowledge SET confidence=MAX(0.02, confidence-0.3), updated_at=? WHERE item_id=?",
                    (now_ts(), item_id),
                )

    def decay(self, decay_rate: float = 0.01) -> None:
        with self.db.tx() as conn:
            conn.execute(
                """UPDATE knowledge SET confidence=MAX(?, confidence-?)
                   WHERE agent_id=? AND source_type!='verified' AND access_count<3""",
                (MIN_CONFIDENCE, decay_rate, self.agent_id),
            )
            conn.execute(
                "DELETE FROM knowledge WHERE agent_id=? AND confidence<? AND verified=0",
                (self.agent_id, DECAY_THRESHOLD),
            )

    def get_context_for_llm(self, domain: Optional[str] = None, limit: int = 8) -> str:
        items = self.retrieve(domain=domain, min_confidence=0.3, limit=limit)
        if not items:
            return f"No knowledge stored{' in domain: '+domain if domain else ''}."
        lines = [f"Known facts{' ['+domain+']' if domain else ''}:"]
        for item in items:
            v = " [✓]" if item.verification_status == "verified" else ""
            lines.append(f"  • {item.content[:100]} (confidence: {item.confidence:.0%}){v}")
        return "\n".join(lines)

    def get_knowledge_gaps(self, observed_domains: List[str]) -> List[str]:
        gaps = []
        for domain in observed_domains:
            items = self.retrieve(domain=domain, limit=5)
            uncertain = [i for i in items if i.confidence < 0.5]
            if not items:
                gaps.append(f"No knowledge in domain: {domain}")
            elif len(uncertain) > len(items) // 2:
                gaps.append(f"High uncertainty in domain: {domain}")
        return gaps

    def count(self) -> int:
        row = self.db.fetchone(
            "SELECT COUNT(*) as c FROM knowledge WHERE agent_id=?", (self.agent_id,)
        )
        return int(row["c"]) if row else 0

    def _find_similar(self, content: str, domain: str) -> Optional[Dict]:
        return self.db.fetchone(
            "SELECT item_id FROM knowledge WHERE agent_id=? AND domain=? AND content=?",
            (self.agent_id, domain, content),
        )

    def _row_to_item(self, row: Dict) -> KnowledgeItem:
        return KnowledgeItem(
            item_id=row["item_id"],
            agent_id=row["agent_id"],
            content=row["content"],
            domain=row["domain"],
            confidence=row["confidence"],
            evidence=jload(row.get("evidence"), []),
            source=row.get("source") or "",
            source_type=row.get("source_type") or "observation",
            verification_status="verified" if row.get("verified") else "unverified",
            created_at=row.get("created_at") or 0.0,
            updated_at=row.get("updated_at") or 0.0,
            access_count=row.get("access_count") or 0,
            tags=jload(row.get("tags"), []),
        )
