"""Goal generation — external, internal, discovery, learning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ags.shared.types import new_id, now_ts


@dataclass
class Goal:
    goal_id: str
    agent_id: str
    description: str
    kind: str
    priority: float = 0.5
    status: str = "open"
    source: str = ""
    parent_goal_id: Optional[str] = None
    created_at: float = field(default_factory=now_ts)
    completed_at: Optional[float] = None


class GoalManager:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._goals: List[Goal] = []

    def add(
        self,
        description: str,
        kind: str = "internal",
        priority: float = 0.5,
        source: str = "",
    ) -> Goal:
        g = Goal(
            goal_id=new_id(),
            agent_id=self.agent_id,
            description=description,
            kind=kind,
            priority=priority,
            source=source,
        )
        self._goals.append(g)
        return g

    def from_questions(self, questions: list) -> List[Goal]:
        goals = []
        for q in questions:
            text = q.text if hasattr(q, "text") else str(q)
            urgency = getattr(q, "urgency", 0.5)
            goals.append(
                self.add(
                    description=f"Investigate: {text}",
                    kind="discovery",
                    priority=float(urgency),
                    source="curiosity",
                )
            )
        return goals

    def from_external(self, description: str, priority: float = 0.8) -> Goal:
        return self.add(
            description, kind="external", priority=priority, source="ccos_or_human"
        )

    def active(self) -> List[Goal]:
        return [g for g in self._goals if g.status in ("open", "active")]

    def top(self, n: int = 3) -> List[Goal]:
        return sorted(self.active(), key=lambda g: -g.priority)[:n]

    def complete(self, goal_id: str) -> None:
        for g in self._goals:
            if g.goal_id == goal_id:
                g.status = "completed"
                g.completed_at = now_ts()

    def abandon_stale(self, max_open: int = 12) -> None:
        open_g = self.active()
        if len(open_g) <= max_open:
            return
        for g in sorted(open_g, key=lambda x: x.priority)[: len(open_g) - max_open]:
            g.status = "abandoned"
