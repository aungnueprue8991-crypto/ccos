"""Question engine — anomalies, contradictions, gaps → research questions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.types import CognitiveObjective, DriveName, QuestionKind, ResearchQuestion


class QuestionEngine:
    def from_objective(
        self,
        objective: CognitiveObjective,
        prediction_errors: Optional[List[Dict[str, Any]]] = None,
        contradictions: Optional[List[str]] = None,
        known_mechanisms: Optional[List[str]] = None,
        capability_gaps: Optional[List[str]] = None,
        domain: str = "general",
    ) -> List[ResearchQuestion]:
        prediction_errors = prediction_errors or []
        contradictions = contradictions or []
        known_mechanisms = known_mechanisms or []
        capability_gaps = capability_gaps or []
        out: List[ResearchQuestion] = []

        for err in prediction_errors[:5]:
            pred = err.get("predicted")
            actual = err.get("actual")
            entity = err.get("entity", "system")
            out.append(
                ResearchQuestion(
                    kind=QuestionKind.ANOMALY,
                    text=(
                        f"Why did prediction for {entity} fail? "
                        f"predicted={pred}, actual={actual}"
                    ),
                    domain=domain,
                    novelty=0.6,
                    informativeness=0.8,
                    solvability=0.6,
                    utility=0.7,
                    source_drive=DriveName.SURPRISE,
                    context=dict(err),
                )
            )

        for c in contradictions[:3]:
            out.append(
                ResearchQuestion(
                    kind=QuestionKind.CONTRADICTION,
                    text=f"How can we resolve contradiction: {c}",
                    domain=domain,
                    novelty=0.5,
                    informativeness=0.85,
                    solvability=0.5,
                    utility=0.75,
                    source_drive=DriveName.COHERENCE,
                    context={"contradiction": c},
                )
            )

        if objective.primary_drive == DriveName.COMPRESSION and known_mechanisms:
            out.append(
                ResearchQuestion(
                    kind=QuestionKind.COMPRESSION,
                    text=(
                        "Can multiple observations be explained by a single simpler "
                        f"mechanism than {known_mechanisms[:3]}?"
                    ),
                    domain=domain,
                    novelty=0.55,
                    informativeness=0.7,
                    solvability=0.45,
                    utility=0.8,
                    source_drive=DriveName.COMPRESSION,
                )
            )

        for gap in capability_gaps[:3]:
            out.append(
                ResearchQuestion(
                    kind=QuestionKind.CAPABILITY,
                    text=f"What capability is missing to achieve: {gap}?",
                    domain=domain,
                    novelty=0.5,
                    informativeness=0.6,
                    solvability=0.5,
                    utility=0.85,
                    source_drive=DriveName.AGENCY,
                    context={"gap": gap},
                )
            )

        if objective.primary_drive == DriveName.CHALLENGE:
            out.append(
                ResearchQuestion(
                    kind=QuestionKind.BOUNDARY,
                    text=(
                        f"Where does current competence in {domain} fail "
                        "just beyond the known region?"
                    ),
                    domain=domain,
                    novelty=0.65,
                    informativeness=0.75,
                    solvability=0.4,
                    utility=0.7,
                    source_drive=DriveName.CHALLENGE,
                )
            )

        if objective.primary_drive == DriveName.SELF_IMPROVEMENT:
            out.append(
                ResearchQuestion(
                    kind=QuestionKind.SELF_MODEL,
                    text="Why is self-predicted success miscalibrated vs actual outcomes?",
                    domain="metacognition",
                    novelty=0.5,
                    informativeness=0.8,
                    solvability=0.55,
                    utility=0.9,
                    source_drive=DriveName.SELF_IMPROVEMENT,
                )
            )

        if not out:
            out.append(
                ResearchQuestion(
                    kind=QuestionKind.GAP,
                    text=f"What is not yet understood in domain '{domain}'?",
                    domain=domain,
                    novelty=0.4,
                    informativeness=0.5,
                    solvability=0.5,
                    utility=0.5,
                    source_drive=objective.primary_drive,
                )
            )

        for q in out:
            q.domain = q.domain or domain
        return out
