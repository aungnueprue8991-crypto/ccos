"""Emergence detector — strict criteria for claimed emergent capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EmergenceClaim:
    name: str
    not_hardcoded: bool = False
    appears_through_interaction: bool = False
    measurable: bool = False
    transfers: bool = False
    survives_ablation: bool = False
    reproduces: bool = False
    evidence: Dict[str, str] = field(default_factory=dict)

    def accepted(self) -> bool:
        return all(
            [
                self.not_hardcoded,
                self.appears_through_interaction,
                self.measurable,
                self.transfers,
                self.survives_ablation,
                self.reproduces,
            ]
        )


class EmergenceDetector:
    def evaluate(self, claim: EmergenceClaim) -> Dict[str, object]:
        return {
            "name": claim.name,
            "accepted": claim.accepted(),
            "checklist": {
                "not_hardcoded": claim.not_hardcoded,
                "interaction": claim.appears_through_interaction,
                "measurable": claim.measurable,
                "transfers": claim.transfers,
                "ablation": claim.survives_ablation,
                "reproduces": claim.reproduces,
            },
            "evidence": claim.evidence,
        }
