"""MAD arena — multi-perspective critique of hypotheses (Explorer/Skeptic/...)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from nexus.types import Hypothesis


@dataclass
class ArenaVerdict:
    hypothesis_id: str
    role_scores: Dict[str, float] = field(default_factory=dict)
    critiques: List[str] = field(default_factory=list)
    aggregate: float = 0.0
    advanced: bool = False


class MADArena:
    ROLES = (
        "explorer",
        "skeptic",
        "engineer",
        "analogist",
        "causalist",
        "contrarian",
        "falsifier",
    )

    def debate(self, hypothesis: Hypothesis) -> ArenaVerdict:
        scores: Dict[str, float] = {}
        critiques: List[str] = []
        text = hypothesis.statement.lower()
        conf = hypothesis.confidence

        scores["explorer"] = min(1.0, 0.4 + 0.3 * len(hypothesis.predictions) + 0.2 * conf)
        scores["skeptic"] = min(1.0, 0.5 + (0.3 if conf > 0.8 else 0.1))
        if conf > 0.85:
            critiques.append("skeptic: confidence may be inflated without evidence")
        scores["engineer"] = 0.55 if hypothesis.predictions else 0.3
        if not hypothesis.predictions:
            critiques.append("engineer: no operational predictions")
        scores["analogist"] = 0.5 + (0.2 if "analog" in text or "like" in text else 0.0)
        scores["causalist"] = 0.5 + (
            0.25 if any(k in text for k in ("cause", "because", "→", "lead")) else 0.0
        )
        scores["contrarian"] = 0.45 + (0.2 if hypothesis.falsifiers else 0.0)
        scores["falsifier"] = min(1.0, 0.3 + 0.25 * len(hypothesis.falsifiers))
        if not hypothesis.falsifiers:
            critiques.append("falsifier: no falsification criteria")

        agg = sum(scores.values()) / len(scores)
        advanced = agg >= 0.45 and bool(hypothesis.predictions) and scores["falsifier"] >= 0.3
        return ArenaVerdict(
            hypothesis_id=hypothesis.hypothesis_id,
            role_scores=scores,
            critiques=critiques,
            aggregate=round(agg, 4),
            advanced=advanced,
        )
