"""Memory Compression Engine — reduce storage with retrieval-fidelity check."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from nexus.memory.hybrid import HybridMemory, MemoryEntry


@dataclass
class CompressionResult:
    before_units: int
    after_units: int
    ratio: float
    retrieval_fidelity: float
    accepted: bool
    notes: List[str]


class MemoryCompressionEngine:
    def compress_and_validate(
        self,
        memory: HybridMemory,
        queries: List[str] | None = None,
        max_len: int = 100,
        min_fidelity: float = 0.5,
    ) -> CompressionResult:
        queries = queries or ["equilibrium", "transfer", "mechanism", "anomaly"]
        entries = list(memory.entries.values())
        before = sum(len(e.content) for e in entries) or 1
        base_hits = sum(1 for q in queries if memory.retrieve(q, k=1))

        compressed = HybridMemory()
        after = 0
        for e in entries:
            text = e.content[:max_len]
            after += len(text)
            compressed.write(
                MemoryEntry(
                    content=text,
                    domain=e.domain,
                    tags=e.tags,
                    type="semantic",
                    confidence=e.confidence,
                    provenance=e.provenance + ["compressed"],
                )
            )
        new_hits = sum(1 for q in queries if compressed.retrieve(q, k=1))
        fidelity = new_hits / max(1, base_hits) if base_hits else (1.0 if new_hits == 0 else 0.0)
        ratio = after / before
        accepted = fidelity >= min_fidelity and ratio < 1.0
        return CompressionResult(
            before_units=before,
            after_units=after,
            ratio=round(ratio, 4),
            retrieval_fidelity=round(fidelity, 4),
            accepted=accepted,
            notes=["fidelity_ok" if accepted else "fidelity_or_ratio_fail"],
        )
