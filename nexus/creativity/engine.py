"""Creativity engine — structured exploration via idea operators."""

from __future__ import annotations

from typing import List

from nexus.ideas.generator import IdeaEngine
from nexus.types import Idea, ResearchQuestion


class CreativityEngine:
    def __init__(self, seed: int = 7):
        self.ideas = IdeaEngine(seed=seed)

    def explore(self, question: ResearchQuestion, n: int = 4) -> List[Idea]:
        return self.ideas.generate(question, n=n)

    def transform(self, idea: Idea) -> Idea:
        return Idea(
            concepts=list(idea.concepts) + ["transformed"],
            mechanisms=idea.mechanisms,
            analogies=idea.analogies,
            assumptions=idea.assumptions + ["transformed_view"],
            predictions=idea.predictions,
            operator="transform",
            novelty_score=min(1.0, idea.novelty_score + 0.1),
            text=f"[transformed] {idea.text}",
            domain=idea.domain,
        )
