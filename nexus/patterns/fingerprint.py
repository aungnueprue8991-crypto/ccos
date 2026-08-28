"""Structural fingerprint engine — compare domains by structure, not names."""

from __future__ import annotations

from typing import Dict, List, Tuple

from nexus.types import StructuralFingerprint


class FingerprintEngine:
    FEATURES = (
        "constraint",
        "periodicity",
        "symmetry",
        "hierarchy",
        "sparsity",
        "recurrence",
        "graph_topology",
        "information_flow",
        "search_landscape",
        "causal_structure",
    )

    def fingerprint(self, domain: str, signals: Dict[str, float], labels: List[str] | None = None) -> StructuralFingerprint:
        feats = {k: float(signals.get(k, 0.0)) for k in self.FEATURES}
        for k in feats:
            feats[k] = max(0.0, min(1.0, feats[k]))
        return StructuralFingerprint(domain=domain, features=feats, labels=list(labels or []))

    def from_thermo_domain(self) -> StructuralFingerprint:
        return self.fingerprint(
            "thermodynamics",
            {
                "constraint": 0.7,
                "periodicity": 0.1,
                "symmetry": 0.4,
                "hierarchy": 0.2,
                "sparsity": 0.3,
                "recurrence": 0.5,
                "graph_topology": 0.2,
                "information_flow": 0.6,
                "search_landscape": 0.3,
                "causal_structure": 0.8,
            },
            labels=["conservation", "equilibrium", "flow"],
        )

    def from_selection_domain(self) -> StructuralFingerprint:
        return self.fingerprint(
            "selection",
            {
                "constraint": 0.6,
                "periodicity": 0.2,
                "symmetry": 0.3,
                "hierarchy": 0.5,
                "sparsity": 0.4,
                "recurrence": 0.7,
                "graph_topology": 0.5,
                "information_flow": 0.5,
                "search_landscape": 0.8,
                "causal_structure": 0.7,
            },
            labels=["variation", "fitness", "retention"],
        )

    def most_similar(
        self, probe: StructuralFingerprint, library: List[StructuralFingerprint]
    ) -> List[Tuple[StructuralFingerprint, float]]:
        ranked = [(fp, probe.distance(fp)) for fp in library]
        ranked.sort(key=lambda x: x[1])
        return ranked


class PatternDiscoveryEngine:
    """Search memory-like fragments for recurring structural motifs."""

    def __init__(self):
        self.fp = FingerprintEngine()
        self.candidates: list = []

    def scan(self, fragments: list, domain: str = "general") -> list:
        """Return candidate pattern descriptions from text fragments."""
        out = []
        if len(fragments) < 2:
            return out
        tokens = {}
        for frag in fragments:
            for w in str(frag).lower().replace("_", " ").split():
                if len(w) > 4:
                    tokens[w] = tokens.get(w, 0) + 1
        recurring = [w for w, c in tokens.items() if c >= 2]
        if recurring:
            desc = f"recurring motifs in {domain}: {', '.join(recurring[:5])}"
            out.append(desc)
            self.candidates.append(desc)
        return out
