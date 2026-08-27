"""Inspiration Engine — mechanism-level cross-domain analogy (not word similarity)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from nexus.patterns.similarity import fingerprint_similarity
from nexus.patterns.fingerprint import FingerprintEngine
from nexus.types import StructuralFingerprint


# Curated mechanism library (structure, not slogans)
MECHANISM_LIBRARY: List[Dict[str, str]] = [
    {"domain": "biology", "mechanism": "selection_under_constraint", "pattern": "variation_selection_retention"},
    {"domain": "ecology", "mechanism": "resource_competition", "pattern": "local_adaptation_scarce_resource"},
    {"domain": "thermodynamics", "mechanism": "equilibration", "pattern": "flow_until_gradient_zero"},
    {"domain": "networks", "mechanism": "congestion_control", "pattern": "feedback_throttle_under_load"},
    {"domain": "neuroscience", "mechanism": "lateral_inhibition", "pattern": "local_suppression_sharpens_signal"},
    {"domain": "economics", "mechanism": "market_clearing", "pattern": "price_mediates_supply_demand"},
    {"domain": "immune", "mechanism": "clonal_selection", "pattern": "amplify_successful_variants"},
    {"domain": "distributed_systems", "mechanism": "consensus", "pattern": "local_state_global_agreement"},
    {"domain": "information_theory", "mechanism": "compression", "pattern": "remove_redundancy_keep_predictive"},
    {"domain": "evolution", "mechanism": "niche_construction", "pattern": "agent_changes_environment_feedback"},
]


@dataclass
class InspirationCandidate:
    source_domain: str
    target_domain: str
    mechanism: str
    pattern: str
    structural_sim: float
    idea: str


class InspirationEngine:
    def __init__(self):
        self.fp = FingerprintEngine()

    def inspire(
        self,
        target_domain: str,
        target_problem: str,
        k: int = 3,
    ) -> List[InspirationCandidate]:
        labels = target_problem.lower().split() + [target_domain]

        def _signals(words):
            keys = ["constraint", "hierarchy", "information_flow", "causal_structure", "sparsity"]
            return {
                k: min(1.0, 0.3 + 0.1 * sum(1 for w in words if w[:3] in k or k[:3] in w))
                for k in keys
            }

        target_fp = self.fp.fingerprint(target_domain, _signals(labels), labels=labels)
        out: List[InspirationCandidate] = []
        for m in MECHANISM_LIBRARY:
            if m["domain"] == target_domain:
                continue
            words = [m["mechanism"], m["pattern"], m["domain"]]
            src_fp = self.fp.fingerprint(m["domain"], _signals(words), labels=words)
            sim = fingerprint_similarity(target_fp, src_fp, metric="weighted_l1")
            if sim < 0.25:
                continue
            idea = (
                f"Map mechanism '{m['mechanism']}' from {m['domain']} onto {target_domain}: "
                f"pattern={m['pattern']} for problem '{target_problem[:80]}'"
            )
            out.append(
                InspirationCandidate(
                    source_domain=m["domain"],
                    target_domain=target_domain,
                    mechanism=m["mechanism"],
                    pattern=m["pattern"],
                    structural_sim=round(sim, 4),
                    idea=idea,
                )
            )
        out.sort(key=lambda c: c.structural_sim, reverse=True)
        return out[:k]
