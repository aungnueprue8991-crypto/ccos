"""Reasoning Engine — take possibilities and determine what follows.

Does not invent freely; operates on Thought inputs.
Methods: deduction, induction, abduction, causal, critique, plan.
"""

from __future__ import annotations

from typing import List, Optional

from nexus.types import ReasoningResult, Thought, ThoughtKind


class ReasoningEngine:
    def process(self, thoughts: List[Thought], domain: str = "general") -> List[ReasoningResult]:
        results: List[ReasoningResult] = []
        for t in thoughts:
            results.append(self._reason_one(t, domain))
        return results

    def _reason_one(self, t: Thought, domain: str) -> ReasoningResult:
        if t.kind == ThoughtKind.COUNTERFACTUAL:
            return ReasoningResult(
                method="abduction",
                premises=[t.content],
                conclusion=(
                    f"If the counterfactual holds, observable outcomes in {domain} "
                    "should diverge from baseline under controlled intervention"
                ),
                confidence=0.45,
                falsifiers=["no divergence under intervention", "effect size ≈ 0"],
                predictions={"divergence_under_intervention": True},
                thought_ids=[t.thought_id],
            )
        if t.kind == ThoughtKind.ANALOGY:
            return ReasoningResult(
                method="induction",
                premises=[t.content],
                conclusion=(
                    "Shared structure implies a transferable mechanism; "
                    "define structural fingerprint and test blind transfer"
                ),
                confidence=0.5,
                falsifiers=["transfer fails under matched structure", "fingerprint distance high"],
                predictions={"transfer_possible": True},
                thought_ids=[t.thought_id],
            )
        if t.kind == ThoughtKind.REFRAME:
            return ReasoningResult(
                method="critique",
                premises=[t.content],
                conclusion=(
                    "Problem may be mis-specified; generate alternative formulations "
                    "before committing experiment budget"
                ),
                confidence=0.55,
                falsifiers=["original formulation uniquely predicts observations"],
                predictions={"alternative_formulation_exists": True},
                thought_ids=[t.thought_id],
                critiques=["assumption audit required"],
            )
        if t.kind == ThoughtKind.PATTERN:
            return ReasoningResult(
                method="induction",
                premises=[t.content],
                conclusion=(
                    "Recurring anomaly cluster warrants a unifying mechanism hypothesis "
                    "with boundary conditions"
                ),
                confidence=0.5,
                falsifiers=["anomalies explained by independent noise"],
                predictions={"unifying_mechanism": True},
                thought_ids=[t.thought_id],
            )
        if t.kind == ThoughtKind.SURPRISE:
            return ReasoningResult(
                method="causal",
                premises=[t.content],
                conclusion=(
                    "Competing causal models (direct effect vs confound vs model error) "
                    "should be distinguished by intervention"
                ),
                confidence=0.52,
                falsifiers=["all models make identical predictions"],
                predictions={"models_distinguishable": True},
                thought_ids=[t.thought_id],
            )
        # default association / recombination
        return ReasoningResult(
            method="abduction",
            premises=[t.content],
            conclusion=f"Best current explanation candidate for focus in {domain}: {t.content[:80]}",
            confidence=0.4,
            falsifiers=["null effect under test"],
            predictions={"testable_effect": True},
            thought_ids=[t.thought_id],
        )

    def to_hypothesis_seed(self, result: ReasoningResult) -> dict:
        return {
            "statement": result.conclusion,
            "predictions": result.predictions,
            "falsifiers": result.falsifiers,
            "confidence": result.confidence,
            "method": result.method,
            "thought_ids": result.thought_ids,
        }
