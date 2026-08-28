"""Concept Formation — invent categories, not just detect similarity."""

from __future__ import annotations

from typing import List, Optional

from nexus.types import Concept, Theory


class ConceptFormationEngine:
    def __init__(self):
        self.concepts: List[Concept] = []

    def form_from_mechanism(
        self,
        mechanism: str,
        examples: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        name_hint: str = "",
    ) -> Concept:
        examples = examples or []
        domains = domains or []
        tokens = [t for t in mechanism.replace("_", " ").split() if t][:4]
        name = name_hint or ("adaptive_" + "_".join(tokens[:3])).lower()
        concept = Concept(
            name=name,
            definition=f"Category of systems exhibiting mechanism: {mechanism}",
            necessary_properties=["recurring mechanism", "testable boundary"],
            examples=list(examples)[:5],
            counterexamples=[],
            predicted_domains=list(domains)[:5] or ["related_domains"],
            mechanism=mechanism,
            confidence=0.45 + 0.05 * min(3, len(examples)),
        )
        self.concepts.append(concept)
        return concept

    def form_from_theory(self, theory: Theory) -> Concept:
        return self.form_from_mechanism(
            mechanism=theory.mechanism,
            examples=theory.supporting_evidence[:3],
            domains=[theory.domain],
        )
