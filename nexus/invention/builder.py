"""Invention / artifact builder — specification → artifact package (not auto-promoted)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts
from nexus.types import Hypothesis, Idea, Theory


@dataclass
class ArtifactSpec:
    artifact_id: str = field(default_factory=new_id)
    idea: Optional[Idea] = None
    hypothesis: Optional[Hypothesis] = None
    theory: Optional[Theory] = None
    design: str = ""
    tests: List[str] = field(default_factory=list)
    benchmarks: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    status: str = "draft"


class InventionEngine:
    def specify(
        self,
        idea: Idea,
        hypothesis: Optional[Hypothesis] = None,
        theory: Optional[Theory] = None,
    ) -> ArtifactSpec:
        design = (
            f"# Design\n\nIdea: {idea.text}\n\n"
            f"Mechanisms: {', '.join(idea.mechanisms)}\n"
            f"Operator: {idea.operator}\n"
        )
        tests = [
            "unit: mechanism_runs",
            "property: deterministic_under_seed",
            "adversarial: null_effect_control",
        ]
        return ArtifactSpec(
            idea=idea,
            hypothesis=hypothesis,
            theory=theory,
            design=design,
            tests=tests,
            benchmarks=["baseline_compare"],
            provenance={
                "created_at": now_ts(),
                "idea_id": idea.idea_id,
                "hypothesis_id": hypothesis.hypothesis_id if hypothesis else None,
            },
            status="draft",
        )

    def to_bundle(self, spec: ArtifactSpec) -> Dict[str, Any]:
        return {
            "artifact_id": spec.artifact_id,
            "status": spec.status,
            "design": spec.design,
            "tests": spec.tests,
            "benchmarks": spec.benchmarks,
            "provenance": spec.provenance,
            "idea": spec.idea.to_dict() if spec.idea else None,
        }
