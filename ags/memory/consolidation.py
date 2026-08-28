"""Memory consolidation — promote WM → long-term; decay unused knowledge."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ags.memory.working import WorkingMemory
    from ags.memory.episodic import EpisodicStore
    from ags.memory.semantic import SemanticMemory


class MemoryConsolidator:
    def __init__(
        self,
        working: "WorkingMemory",
        episodic: "EpisodicStore",
        semantic: "SemanticMemory",
        consolidation_rate: float = 0.5,
    ):
        self.working = working
        self.episodic = episodic
        self.semantic = semantic
        self.consolidation_rate = consolidation_rate
        self._cycle = 0

    def consolidate(self, agent_id: str, importance_threshold: float = 0.4) -> int:
        self._cycle += 1
        promoted = 0
        for key, value in self.working.get_all().items():
            if not (key.startswith("obs:") or key.startswith("result:")):
                continue
            if isinstance(value, dict):
                importance = float(value.get("importance", 0.3))
                if importance >= importance_threshold:
                    self.semantic.store(
                        content=str(value.get("description", value))[:200],
                        domain=str(value.get("domain", "general")),
                        confidence=min(0.7, importance),
                        source="working_memory",
                        source_type="observation",
                    )
                    promoted += 1
        if self._cycle % 5 == 0:
            self.semantic.decay()
        self.working.tick()
        return promoted

    def sleep_consolidation(self, agent_id: str) -> int:
        promoted = 0
        for ep in self.episodic.get_recent(limit=20):
            if ep.importance >= 0.6 and ep.outcome:
                self.semantic.store(
                    content=f"When: {ep.description[:80]} → Result: {ep.outcome[:80]}",
                    domain="procedural_history",
                    confidence=0.5 + ep.emotional_valence * 0.2,
                    source="sleep_consolidation",
                    source_type="inference",
                )
                promoted += 1
        return promoted
