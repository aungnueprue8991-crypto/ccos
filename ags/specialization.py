"""Phase 5 — emergent specialization vectors from experience."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict


class SpecializationTracker:
    def __init__(self) -> None:
        self._scores: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def observe(self, agent_id: str, domain: str, knowledge_count: int) -> None:
        self._scores[agent_id][domain] = max(self._scores[agent_id][domain], float(knowledge_count) * 0.1 + 0.2)

    def vector(self, agent_id: str) -> Dict[str, float]:
        return dict(self._scores.get(agent_id, {}))

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        return {aid: dict(v) for aid, v in self._scores.items()}
