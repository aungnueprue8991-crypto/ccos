"""Novelty Engine — multi-dimensional, testable novelty (wording ≠ idea)."""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Set


@dataclass
class NoveltyScore:
    lexical: float = 0.0
    semantic: float = 0.0
    structural: float = 0.0
    mechanistic: float = 0.0
    representation: float = 0.0
    cross_domain: float = 0.0
    predictive: float = 0.0
    behavioral: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)

    def genuine_idea(self) -> bool:
        """Novel wording alone is insufficient."""
        return (
            self.structural >= 0.5
            or self.mechanistic >= 0.5
            or self.predictive >= 0.5
            or self.cross_domain >= 0.55
            or self.behavioral >= 0.5
        )

    def aggregate(self) -> float:
        vals = list(self.as_dict().values())
        return sum(vals) / len(vals) if vals else 0.0


class NoveltyEngine:
    def __init__(self):
        self.seen_texts: Set[str] = set()
        self.seen_mechanisms: Set[str] = set()

    def _tokens(self, text: str) -> Set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def score(
        self,
        candidate: str,
        *,
        known_texts: Optional[Sequence[str]] = None,
        mechanism: str = "",
        domain: str = "general",
        other_domain: str = "",
        has_new_prediction: bool = False,
        structural_sim_to_known: float = 0.5,
        transfer_hit: Optional[bool] = None,
    ) -> NoveltyScore:
        known = list(known_texts or [])
        ct = self._tokens(candidate)
        lex = 1.0
        for k in known[:50]:
            kt = self._tokens(k)
            if not ct or not kt:
                continue
            j = len(ct & kt) / len(ct | kt)
            lex = min(lex, 1.0 - j)
        if candidate.lower().strip() in self.seen_texts:
            lex = min(lex, 0.1)

        sem = lex * 0.8 + 0.1
        structural = max(0.0, min(1.0, 1.0 - structural_sim_to_known))

        mech = 0.3
        if mechanism:
            if mechanism not in self.seen_mechanisms:
                mech = 0.85
            else:
                mech = 0.25

        representation = 0.4
        if any(w in candidate.lower() for w in ("reframe", "represent", "as graph", "as geometry")):
            representation = 0.75

        cross = 0.2
        if other_domain and other_domain != domain:
            cross = 0.7 + 0.2 * structural

        predictive = 0.8 if has_new_prediction else 0.25
        behavioral = 0.8 if transfer_hit else (0.3 if transfer_hit is False else 0.4)

        score = NoveltyScore(
            lexical=round(lex, 4),
            semantic=round(sem, 4),
            structural=round(structural, 4),
            mechanistic=round(mech, 4),
            representation=round(representation, 4),
            cross_domain=round(min(1.0, cross), 4),
            predictive=round(predictive, 4),
            behavioral=round(behavioral, 4),
        )
        self.seen_texts.add(candidate.lower().strip()[:200])
        if mechanism:
            self.seen_mechanisms.add(mechanism)
        return score
