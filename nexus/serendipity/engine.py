"""Serendipity Engine — controlled exploration of unexpected cluster links.

Layer A: drive-coupled rate + hard token quota per epoch.
Layer B: structural relevance gate (unexpected surface × similar structure).

Serendipity = unexpected AND relevant — not pure randomness.
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from nexus.patterns.fingerprint import FingerprintEngine
from nexus.types import StructuralFingerprint, Thought, ThoughtKind


@dataclass
class LinkCandidate:
    cluster_a: str
    cluster_b: str
    lexical_distance: float
    structural_similarity: float
    score: float
    rationale: str = ""


@dataclass
class BudgetState:
    base: float = 0.15
    current: float = 0.15
    min_b: float = 0.03
    max_b: float = 0.40
    tokens_per_epoch: int = 3
    tokens_left: int = 3
    epoch_len: int = 20
    cycle_in_epoch: int = 0
    emits: int = 0
    skips: int = 0
    last_factors: Dict[str, float] = field(default_factory=dict)


class SerendipityEngine:
    def __init__(
        self,
        seed: int = 11,
        base_budget: float = 0.15,
        min_budget: float = 0.03,
        max_budget: float = 0.40,
        tokens_per_epoch: int = 3,
        epoch_len: int = 20,
        structural_tau: float = 0.45,
        min_lexical_distance: float = 0.35,
    ):
        self.rng = random.Random(seed)
        self.fp = FingerprintEngine()
        self.structural_tau = structural_tau
        self.min_lexical_distance = min_lexical_distance
        self.state = BudgetState(
            base=base_budget,
            current=base_budget,
            min_b=min_budget,
            max_b=max_budget,
            tokens_per_epoch=tokens_per_epoch,
            tokens_left=tokens_per_epoch,
            epoch_len=epoch_len,
        )
        self._fp_cache: Dict[str, StructuralFingerprint] = {}
        self.history: List[Dict[str, Any]] = []

    def compute_budget(
        self,
        novelty_hunger: float = 0.3,
        plateau: float = 0.0,
        coherence_pressure: float = 0.0,
        resource_pressure: float = 0.2,
        surprise_crisis: float = 0.0,
        consolidation_phase: bool = False,
    ) -> float:
        alpha, beta, gamma, delta, eps = 0.25, 0.20, 0.10, 0.30, 0.35
        raw = (
            self.state.base
            + alpha * _clip01(novelty_hunger)
            + beta * _clip01(plateau)
            + gamma * _clip01(coherence_pressure)
            - delta * _clip01(resource_pressure)
            - eps * _clip01(surprise_crisis)
        )
        if consolidation_phase:
            raw = min(self.state.max_b, raw * 2.0)
        b = max(self.state.min_b, min(self.state.max_b, raw))
        self.state.current = b
        self.state.last_factors = {
            "novelty_hunger": novelty_hunger,
            "plateau": plateau,
            "coherence_pressure": coherence_pressure,
            "resource_pressure": resource_pressure,
            "surprise_crisis": surprise_crisis,
            "consolidation_phase": float(consolidation_phase),
            "budget": b,
            "tokens_left": float(self.state.tokens_left),
        }
        return b

    def _advance_epoch(self) -> None:
        self.state.cycle_in_epoch += 1
        if self.state.cycle_in_epoch >= self.state.epoch_len:
            self.state.cycle_in_epoch = 0
            self.state.tokens_left = self.state.tokens_per_epoch

    def _fingerprint_for(self, label: str) -> StructuralFingerprint:
        key = label.strip().lower()[:80]
        if key in self._fp_cache:
            return self._fp_cache[key]
        tokens = set(re.findall(r"[a-z0-9]+", key))
        feats = {f: 0.15 for f in self.fp.FEATURES}
        motif_map = {
            "conserv": "constraint",
            "equilib": "symmetry",
            "flow": "information_flow",
            "heat": "information_flow",
            "thermal": "causal_structure",
            "select": "search_landscape",
            "fitness": "search_landscape",
            "period": "periodicity",
            "compress": "sparsity",
            "hierarch": "hierarchy",
            "graph": "graph_topology",
            "recur": "recurrence",
            "feedback": "recurrence",
            "resource": "constraint",
            "equal": "symmetry",
        }
        for tok in tokens:
            for prefix, feat in motif_map.items():
                if prefix in tok:
                    feats[feat] = min(1.0, feats[feat] + 0.35)
        h = hashlib.sha256(key.encode()).hexdigest()
        for i, feat in enumerate(self.fp.FEATURES):
            bump = int(h[i * 2 : i * 2 + 2], 16) / 255.0 * 0.25
            feats[feat] = min(1.0, feats[feat] + bump)
        fp = self.fp.fingerprint(key, feats, labels=list(tokens)[:6])
        self._fp_cache[key] = fp
        return fp

    def lexical_distance(self, a: str, b: str) -> float:
        ta = set(re.findall(r"[a-z0-9]+", a.lower()))
        tb = set(re.findall(r"[a-z0-9]+", b.lower()))
        if not ta and not tb:
            return 0.0
        if not ta or not tb:
            return 1.0
        inter = len(ta & tb)
        union = len(ta | tb)
        jaccard = inter / union if union else 0.0
        return 1.0 - jaccard

    def structural_similarity(self, a: str, b: str, metric: str = "weighted_l1") -> float:
        from nexus.patterns.similarity import fingerprint_similarity
        fa, fb = self._fingerprint_for(a), self._fingerprint_for(b)
        return fingerprint_similarity(fa, fb, metric=metric)

    def score_pair(self, a: str, b: str) -> LinkCandidate:
        lex = self.lexical_distance(a, b)
        sim = self.structural_similarity(a, b)
        score = lex * sim
        return LinkCandidate(
            cluster_a=a,
            cluster_b=b,
            lexical_distance=lex,
            structural_similarity=sim,
            score=score,
            rationale=f"lex_dist={lex:.2f} struct_sim={sim:.2f}",
        )

    def rank_candidates(self, clusters: Sequence[str], max_pairs: int = 30) -> List[LinkCandidate]:
        labels = list(dict.fromkeys(str(c).strip() for c in clusters if str(c).strip()))
        if len(labels) < 2:
            return []
        pairs: List[LinkCandidate] = []
        if len(labels) <= 8:
            for i in range(len(labels)):
                for j in range(i + 1, len(labels)):
                    pairs.append(self.score_pair(labels[i], labels[j]))
        else:
            for _ in range(max_pairs):
                a, b = self.rng.sample(labels, 2)
                pairs.append(self.score_pair(a, b))
        gated = [
            p
            for p in pairs
            if p.structural_similarity >= self.structural_tau
            and p.lexical_distance >= self.min_lexical_distance
        ]
        gated.sort(key=lambda p: p.score, reverse=True)
        return gated

    def maybe_link(
        self,
        clusters: Sequence[str],
        domain: str = "general",
        novelty_hunger: float = 0.3,
        plateau: float = 0.0,
        coherence_pressure: float = 0.0,
        resource_pressure: float = 0.2,
        surprise_crisis: float = 0.0,
        consolidation_phase: bool = False,
    ) -> List[Thought]:
        self._advance_epoch()
        b = self.compute_budget(
            novelty_hunger=novelty_hunger,
            plateau=plateau,
            coherence_pressure=coherence_pressure,
            resource_pressure=resource_pressure,
            surprise_crisis=surprise_crisis,
            consolidation_phase=consolidation_phase,
        )

        if self.state.tokens_left <= 0:
            self.state.skips += 1
            self.history.append({"action": "skip_tokens", "budget": b})
            return []

        if self.rng.random() > b:
            self.state.skips += 1
            self.history.append({"action": "skip_rate", "budget": b})
            return []

        ranked = self.rank_candidates(clusters)
        if not ranked:
            self.state.skips += 1
            self.history.append({"action": "skip_gate", "budget": b})
            return []

        best = ranked[0]
        self.state.tokens_left -= 1
        self.state.emits += 1
        thought = Thought(
            kind=ThoughtKind.SERENDIPITY,
            content=(
                f"Unexpected structural link between '{best.cluster_a[:40]}' "
                f"and '{best.cluster_b[:40]}' ({best.rationale})"
            ),
            source="serendipity",
            salience=min(1.0, 0.4 + 0.6 * best.score),
            novelty=min(1.0, 0.5 + 0.5 * best.lexical_distance),
            domain=domain,
            payload={
                "cluster_a": best.cluster_a,
                "cluster_b": best.cluster_b,
                "score": best.score,
                "lexical_distance": best.lexical_distance,
                "structural_similarity": best.structural_similarity,
                "budget": b,
                "tokens_left": self.state.tokens_left,
                "factors": dict(self.state.last_factors),
            },
        )
        self.history.append(
            {
                "action": "emit",
                "budget": b,
                "score": best.score,
                "a": best.cluster_a[:40],
                "b": best.cluster_b[:40],
            }
        )
        return [thought]

    def stats(self) -> Dict[str, Any]:
        return {
            "emits": self.state.emits,
            "skips": self.state.skips,
            "tokens_left": self.state.tokens_left,
            "current_budget": self.state.current,
            "last_factors": dict(self.state.last_factors),
        }


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))
