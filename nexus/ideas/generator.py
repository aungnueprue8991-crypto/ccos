"""Idea formation — operators over concept/mechanism space (not LLM creativity theater)."""

from __future__ import annotations

import random
from typing import List, Optional, Sequence

from nexus.types import Idea, ResearchQuestion


class IdeaEngine:
    OPERATORS = (
        "combine",
        "analogy",
        "invert",
        "decompose",
        "counterfactual",
        "boundary_mutate",
        "mechanism_substitute",
        "representation_change",
    )

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate(
        self,
        question: ResearchQuestion,
        concepts: Optional[Sequence[str]] = None,
        mechanisms: Optional[Sequence[str]] = None,
        n: int = 5,
    ) -> List[Idea]:
        concepts = list(concepts or ["energy", "equilibrium", "structure", "constraint", "feedback"])
        mechanisms = list(
            mechanisms
            or ["heat_flow", "selection", "compression", "recursion", "conservation"]
        )
        ideas: List[Idea] = []
        ops = list(self.OPERATORS)
        self.rng.shuffle(ops)

        for op in ops:
            if len(ideas) >= n:
                break
            idea = self._apply(op, question, concepts, mechanisms)
            if idea:
                ideas.append(idea)
        return ideas

    def _apply(
        self,
        op: str,
        question: ResearchQuestion,
        concepts: List[str],
        mechanisms: List[str],
    ) -> Optional[Idea]:
        c = self.rng.sample(concepts, k=min(2, len(concepts)))
        m = self.rng.sample(mechanisms, k=min(2, len(mechanisms)))

        if op == "combine":
            text = f"Combine {c[0]} with {m[0]} to address: {question.text[:80]}"
            return Idea(
                concepts=c,
                mechanisms=m[:1],
                operator=op,
                text=text,
                domain=question.domain,
                novelty_score=0.55 + 0.1 * self.rng.random(),
                predictions=[f"{c[0]}_modulates_{m[0]}"],
            )
        if op == "analogy":
            text = (
                f"Analogy: structure of {c[0]} resembles {c[-1]}; "
                f"transfer mechanism {m[0]} across domains"
            )
            return Idea(
                concepts=c,
                mechanisms=m[:1],
                analogies=[f"{c[0]}~{c[-1]}"],
                operator=op,
                text=text,
                domain=question.domain,
                novelty_score=0.6 + 0.15 * self.rng.random(),
            )
        if op == "invert":
            text = f"Invert assumption about {c[0]}: minimize instead of maximize"
            return Idea(
                concepts=c[:1],
                mechanisms=m[:1],
                assumptions=[f"not maximize {c[0]}"],
                operator=op,
                text=text,
                domain=question.domain,
                novelty_score=0.5 + 0.2 * self.rng.random(),
            )
        if op == "counterfactual":
            text = f"What if mechanism {m[0]} were absent under {c[0]}?"
            return Idea(
                concepts=c[:1],
                mechanisms=m[:1],
                operator=op,
                text=text,
                domain=question.domain,
                novelty_score=0.58,
                predictions=[f"without_{m[0]}_outcome_changes"],
            )
        if op == "boundary_mutate":
            text = f"Probe boundary of {m[0]} just beyond known valid region of {c[0]}"
            return Idea(
                concepts=c[:1],
                mechanisms=m[:1],
                operator=op,
                text=text,
                domain=question.domain,
                novelty_score=0.62,
            )
        if op == "mechanism_substitute":
            if len(m) < 2:
                m = m + ["feedback"]
            text = f"Substitute {m[0]} with {m[1]} for the same observations"
            return Idea(
                concepts=c[:1],
                mechanisms=m[:2],
                operator=op,
                text=text,
                domain=question.domain,
                novelty_score=0.57,
            )
        if op == "representation_change":
            reps = ["graph", "sequence", "geometry", "symbolic", "frequency"]
            r = self.rng.choice(reps)
            text = f"Re-represent {c[0]} as {r} and re-evaluate {m[0]}"
            return Idea(
                concepts=c[:1] + [r],
                mechanisms=m[:1],
                operator=op,
                text=text,
                domain=question.domain,
                novelty_score=0.65,
            )
        if op == "decompose":
            text = f"Decompose problem involving {c[0]} into subproblems for {m[0]}"
            return Idea(
                concepts=c[:1],
                mechanisms=m[:1],
                operator=op,
                text=text,
                domain=question.domain,
                novelty_score=0.45,
            )
        return None

    def idea_to_hypothesis(self, idea: Idea, question: ResearchQuestion):
        from nexus.types import Hypothesis

        return Hypothesis(
            statement=idea.text,
            predictions={p: True for p in idea.predictions} or {"observable_effect": True},
            confidence=0.4 + 0.2 * idea.novelty_score,
            falsifiers=[f"no effect of {m}" for m in idea.mechanisms[:1]],
            idea_id=idea.idea_id,
            question_id=question.question_id,
        )
