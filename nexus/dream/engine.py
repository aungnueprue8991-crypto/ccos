"""Dream / Offline Discovery — cross-domain recombination (not within-domain rehearsal).

Research note: cross-domain consolidation creates discovery value; pure rehearsal does not.
Candidates still go through the evidence gate when promoted.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from nexus.types import Thought, ThoughtKind
from nexus.workspace.events import CogEvent, CogEventType


@dataclass
class DreamReport:
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    cross_domain_links: List[Dict[str, str]] = field(default_factory=list)
    compressed: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class DreamEngine:
    def __init__(self, seed: int = 13, max_candidates: int = 5):
        self.rng = random.Random(seed)
        self.max_candidates = max_candidates

    def run(
        self,
        episodes: Sequence[Dict[str, Any]],
        concepts: Sequence[str] = (),
        domains: Sequence[str] = (),
        mechanisms: Sequence[str] = (),
    ) -> DreamReport:
        report = DreamReport()
        by_domain: Dict[str, List[str]] = {}
        for ep in episodes:
            d = str(ep.get("domain", "general"))
            by_domain.setdefault(d, []).append(str(ep.get("description", ep.get("text", ""))))
        for d, items in by_domain.items():
            if len(items) >= 2:
                report.compressed.append(f"{d}: compressed {len(items)} episodes")

        domain_list = list(domains) or list(by_domain.keys()) or ["thermodynamics", "selection"]
        concept_list = list(concepts) or ["equilibrium", "competition", "flow", "constraint"]
        mech_list = list(mechanisms) or ["conservation", "selection", "compression"]

        for _ in range(self.max_candidates):
            if len(domain_list) >= 2:
                d1, d2 = self.rng.sample(list(domain_list), 2)
            else:
                d1 = domain_list[0]
                d2 = "hidden_" + d1
            c = self.rng.choice(concept_list)
            m = self.rng.choice(mech_list)
            link = {"domain_a": d1, "domain_b": d2, "concept": c, "mechanism": m}
            report.cross_domain_links.append(link)
            text = (
                f"Dream recombination: mechanism '{m}' linking {d1}↔{d2} "
                f"via concept '{c}'"
            )
            report.candidates.append(
                {
                    "text": text,
                    "kind": "dream_hypothesis",
                    "cross_domain": True,
                    "domain_a": d1,
                    "domain_b": d2,
                    "mechanism": m,
                }
            )

        report.notes.append(
            f"offline: {len(report.compressed)} compressions, "
            f"{len(report.cross_domain_links)} cross-domain links"
        )
        return report

    def to_events(self, report: DreamReport) -> List[CogEvent]:
        events = []
        for c in report.candidates:
            events.append(
                CogEvent(
                    type=CogEventType.THOUGHT.value,
                    payload={
                        "content": c["text"],
                        "kind": ThoughtKind.SERENDIPITY.value,
                        "source": "dream",
                        "novelty": 0.75,
                        "salience": 0.5,
                        "domain": c.get("domain_b", "general"),
                        "cross_domain": True,
                        "mechanism": c.get("mechanism"),
                    },
                    source="dream_engine",
                    priority=0.45,
                    targets=["reasoning_engine", "hypothesis_engine"],
                )
            )
        return events

    def to_thoughts(self, report: DreamReport) -> List[Thought]:
        out = []
        for c in report.candidates:
            out.append(
                Thought(
                    kind=ThoughtKind.SERENDIPITY,
                    content=c["text"],
                    source="dream",
                    salience=0.5,
                    novelty=0.75,
                    domain=c.get("domain_b", "general"),
                    payload=c,
                )
            )
        return out
