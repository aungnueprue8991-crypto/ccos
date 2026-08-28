"""Memory Evolution Engine — benchmark representation policies (storage vs utility)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from nexus.memory.hybrid import HybridMemory, MemoryEntry


@dataclass
class MemoryPolicyCandidate:
    name: str
    storage_units: int
    retrieval_hits: int
    transfer_proxy: float
    score: float
    notes: List[str] = field(default_factory=list)


class MemoryEvolutionEngine:
    """Compare raw vs summary vs concept-tag policies on a memory snapshot."""

    def evaluate(self, memory: HybridMemory, queries: Optional[List[str]] = None) -> List[MemoryPolicyCandidate]:
        queries = queries or ["equilibrium", "transfer", "anomaly", "mechanism"]
        entries = list(memory.entries.values())
        candidates = []

        raw_storage = sum(len(e.content) for e in entries)
        raw_hits = sum(1 for q in queries if memory.retrieve(q, k=1))
        candidates.append(
            MemoryPolicyCandidate(
                name="raw_episodic",
                storage_units=raw_storage,
                retrieval_hits=raw_hits,
                transfer_proxy=0.4,
                score=raw_hits / max(1, raw_storage / 100.0),
                notes=["full fidelity", "high storage"],
            )
        )

        sum_storage = sum(min(80, len(e.content)) for e in entries)
        tmp = HybridMemory()
        for e in entries:
            tmp.write(
                MemoryEntry(
                    content=e.content[:80],
                    domain=e.domain,
                    tags=e.tags,
                    type="semantic",
                    confidence=e.confidence,
                )
            )
        sum_hits = sum(1 for q in queries if tmp.retrieve(q, k=1))
        candidates.append(
            MemoryPolicyCandidate(
                name="summary_80",
                storage_units=sum_storage,
                retrieval_hits=sum_hits,
                transfer_proxy=0.5,
                score=sum_hits / max(1, sum_storage / 100.0),
                notes=["compressed", "possible loss"],
            )
        )

        tag_storage = sum(len(" ".join(e.tags)) for e in entries)
        tag_mem = HybridMemory()
        for e in entries:
            tag_mem.write(
                MemoryEntry(
                    content=" ".join(e.tags) or e.domain,
                    domain=e.domain,
                    tags=e.tags,
                    type="semantic",
                )
            )
        tag_hits = sum(1 for q in queries if tag_mem.retrieve(q, k=1))
        candidates.append(
            MemoryPolicyCandidate(
                name="concept_tags",
                storage_units=max(1, tag_storage),
                retrieval_hits=tag_hits,
                transfer_proxy=0.7,
                score=tag_hits / max(1, tag_storage / 50.0) + 0.1,
                notes=["high transfer proxy", "lossy"],
            )
        )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates

    def best_policy(self, memory: HybridMemory) -> MemoryPolicyCandidate:
        ranked = self.evaluate(memory)
        return ranked[0]
