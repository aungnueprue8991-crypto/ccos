"""Hybrid Universal Memory — semantic + temporal + causal (no FAISS required).

Retrieval fuses:
  - semantic (token / bag-of-words cosine)
  - temporal (recency)
  - causal (explicit links)
plus concept graph, contradiction index, novelty index, provenance.
"""

from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple

from ags.shared.types import new_id, now_ts


def _tokens(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _bow_cosine(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / math.sqrt(len(a) * len(b))


@dataclass
class MemoryEntry:
    id: str = field(default_factory=new_id)
    type: str = "episodic"  # episodic|semantic|causal|theory|hypothesis|experiment
    content: str = ""
    domain: str = "general"
    timestamp: float = field(default_factory=now_ts)
    source: str = ""
    confidence: float = 0.5
    status: str = "active"
    tags: List[str] = field(default_factory=list)
    relations: List[Dict[str, str]] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    novelty_score: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalResult:
    entry: MemoryEntry
    score: float
    semantic: float
    temporal: float
    causal: float
    reasons: List[str] = field(default_factory=list)


class HybridMemory:
    def __init__(self):
        self.entries: Dict[str, MemoryEntry] = {}
        self.concept_graph: Dict[str, Set[str]] = {}
        self.contradiction_index: List[Tuple[str, str, str]] = []
        self.novelty_index: List[Tuple[str, float]] = []

    def write(self, entry: MemoryEntry) -> MemoryEntry:
        if not entry.provenance:
            entry.provenance = [f"write:{entry.source or 'memory'}"]
        self.entries[entry.id] = entry
        concepts = set(entry.tags) | _tokens(entry.domain) | set(list(_tokens(entry.content))[:8])
        for c in concepts:
            self.concept_graph.setdefault(c, set()).add(entry.id)
        if entry.novelty_score > 0.5:
            self.novelty_index.append((entry.id, entry.novelty_score))
            self.novelty_index.sort(key=lambda x: x[1], reverse=True)
            self.novelty_index = self.novelty_index[:200]
        for other_id in entry.contradictions:
            self.contradiction_index.append((entry.id, other_id, "declared"))
        return entry

    def link_causal(self, src_id: str, dst_id: str, rel: str = "causes") -> None:
        src = self.entries.get(src_id)
        dst = self.entries.get(dst_id)
        if not src or not dst:
            return
        src.relations.append({"to": dst_id, "rel": rel})
        self.concept_graph.setdefault(rel, set()).add(src_id)

    def mark_contradiction(self, a_id: str, b_id: str, note: str = "") -> None:
        self.contradiction_index.append((a_id, b_id, note))
        if a_id in self.entries:
            self.entries[a_id].contradictions.append(b_id)
        if b_id in self.entries:
            self.entries[b_id].contradictions.append(a_id)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        domain: Optional[str] = None,
        prefer_causal: bool = False,
        now: Optional[float] = None,
    ) -> List[RetrievalResult]:
        now = now or time.time()
        qtok = _tokens(query)
        results: List[RetrievalResult] = []
        for e in self.entries.values():
            if domain and e.domain != domain and domain not in e.tags:
                domain_pen = 0.15
            else:
                domain_pen = 0.0
            sem = _bow_cosine(qtok, _tokens(e.content) | set(e.tags))
            age = max(0.0, now - e.timestamp)
            temporal = math.exp(-age / 86400.0) if age < 86400 * 30 else 0.05
            causal = 0.0
            for rel in e.relations:
                if _bow_cosine(qtok, _tokens(rel.get("rel", "") + " " + rel.get("to", ""))) > 0:
                    causal = max(causal, 0.6)
            if e.relations and prefer_causal:
                causal = max(causal, 0.4)
            score = 0.50 * sem + 0.25 * temporal + 0.25 * causal - domain_pen
            if score <= 0:
                continue
            reasons = []
            if sem > 0.2:
                reasons.append("semantic")
            if temporal > 0.5:
                reasons.append("recent")
            if causal > 0.3:
                reasons.append("causal")
            results.append(
                RetrievalResult(
                    entry=e,
                    score=round(score, 4),
                    semantic=round(sem, 4),
                    temporal=round(temporal, 4),
                    causal=round(causal, 4),
                    reasons=reasons,
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:k]

    def by_concept(self, concept: str) -> List[MemoryEntry]:
        ids = self.concept_graph.get(concept.lower(), set())
        return [self.entries[i] for i in ids if i in self.entries]

    def novel_entries(self, k: int = 5) -> List[MemoryEntry]:
        out = []
        for eid, _ in self.novelty_index[:k]:
            if eid in self.entries:
                out.append(self.entries[eid])
        return out

    def stats(self) -> Dict[str, Any]:
        return {
            "n_entries": len(self.entries),
            "n_concepts": len(self.concept_graph),
            "n_contradictions": len(self.contradiction_index),
            "n_novelty": len(self.novelty_index),
        }
