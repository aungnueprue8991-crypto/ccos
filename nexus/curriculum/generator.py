"""Autonomous curriculum — frontier questions scored for value."""

from __future__ import annotations

from typing import List, Optional

from nexus.questions.evaluator import QuestionEvaluator
from nexus.questions.generator import QuestionEngine
from nexus.types import CognitiveObjective, DriveName, ResearchQuestion


class CurriculumEngine:
    def __init__(self):
        self.questions = QuestionEngine()
        self.evaluator = QuestionEvaluator()

    def next_questions(
        self,
        domain: str = "general",
        competence: float = 0.5,
        known_mechanisms: Optional[List[str]] = None,
        k: int = 3,
    ) -> List[ResearchQuestion]:
        drive = DriveName.CHALLENGE if competence > 0.6 else DriveName.CURIOSITY
        obj = CognitiveObjective(
            primary_drive=drive,
            description="curriculum frontier",
            domain=domain,
        )
        raw = self.questions.from_objective(
            obj,
            known_mechanisms=known_mechanisms or [],
            domain=domain,
        )
        for q in raw:
            if competence > 0.6 and q.kind.value == "boundary":
                q.utility = min(1.0, q.utility + 0.2)
        return self.evaluator.select_top(raw, k=k)
