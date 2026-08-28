"""Offline consolidation — cluster episodes, compress, surface contradictions."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ConsolidationReport:
    clusters: Dict[str, List[str]] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)


class ConsolidationEngine:
    def run(self, episodes: List[Dict[str, Any]]) -> ConsolidationReport:
        clusters: Dict[str, List[str]] = defaultdict(list)
        for ep in episodes:
            domain = str(ep.get("domain", "general"))
            desc = str(ep.get("description", ep.get("text", "")))
            clusters[domain].append(desc)

        patterns = []
        for domain, items in clusters.items():
            if len(items) >= 2:
                patterns.append(f"{domain}: {len(items)} related episodes")

        contradictions = []
        outcomes = [str(ep.get("outcome", "")) for ep in episodes]
        if "success" in outcomes and "failure" in outcomes:
            contradictions.append("mixed success/failure under similar conditions")

        hypotheses = [f"pattern may explain cluster {d}" for d in list(clusters)[:3]]
        return ConsolidationReport(
            clusters={k: v[:10] for k, v in clusters.items()},
            patterns=patterns,
            contradictions=contradictions,
            hypotheses=hypotheses,
        )
