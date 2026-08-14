"""Phase 6 — collaborative research pool."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from ags.shared.types import new_id, now_ts


@dataclass
class ResearchItem:
    item_id: str
    agent_id: str
    kind: str  # hypothesis | evidence | discovery
    payload: Dict[str, Any]
    votes: int = 0
    verified: bool = False
    created_at: float = field(default_factory=now_ts)


class ResearchPool:
    def __init__(self) -> None:
        self.items: List[ResearchItem] = []

    def submit_hypothesis(self, agent_id: str, hyp: Dict[str, Any]) -> str:
        item = ResearchItem(new_id(), agent_id, "hypothesis", dict(hyp))
        self.items.append(item)
        return item.item_id

    def submit_evidence(self, agent_id: str, evidence: Dict[str, Any], supports: str) -> str:
        item = ResearchItem(new_id(), agent_id, "evidence", {**evidence, "supports": supports})
        self.items.append(item)
        return item.item_id

    def peer_verify(self, item_id: str, verifier_id: str, accept: bool) -> None:
        for it in self.items:
            if it.item_id == item_id:
                it.votes += 1 if accept else -1
                if it.votes >= 1:
                    it.verified = True
                return

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self.items),
            "hypotheses": sum(1 for i in self.items if i.kind == "hypothesis"),
            "verified": sum(1 for i in self.items if i.verified),
        }
