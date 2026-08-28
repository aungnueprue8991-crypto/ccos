"""Question evaluator — novel? informative? solvable? useful? in budget?"""

from __future__ import annotations

from typing import List, Optional, Set

from nexus.types import ResearchQuestion


class QuestionEvaluator:
    def __init__(
        self,
        min_score: float = 0.25,
        max_cost: float = 0.85,
        seen_texts: Optional[Set[str]] = None,
    ):
        self.min_score = min_score
        self.max_cost = max_cost
        self.seen_texts = seen_texts if seen_texts is not None else set()

    def evaluate(self, questions: List[ResearchQuestion]) -> List[ResearchQuestion]:
        accepted: List[ResearchQuestion] = []
        for q in questions:
            if q.text in self.seen_texts:
                q.novelty = max(0.05, q.novelty * 0.5)
            if q.cost > self.max_cost:
                q.accepted = False
                continue
            if q.score() < self.min_score:
                q.accepted = False
                continue
            q.accepted = True
            self.seen_texts.add(q.text)
            accepted.append(q)
        accepted.sort(key=lambda x: x.score(), reverse=True)
        return accepted

    def select_top(self, questions: List[ResearchQuestion], k: int = 1) -> List[ResearchQuestion]:
        return self.evaluate(questions)[:k]
