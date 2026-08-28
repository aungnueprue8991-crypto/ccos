"""Structural similarity metrics for NEXUS fingerprints and mechanism graphs.

Vector metrics: l1, l2, cosine, correlation, chebyshev, weighted_l1, mahalanobis.
Graph metrics: graph_edit_distance (GED) on simple labeled graphs.
API: similarity(), distance(), cosine_similarity().
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from nexus.types import StructuralFingerprint

VectorLike = Union[StructuralFingerprint, Mapping[str, float], Sequence[float]]

DEFAULT_WEIGHTS: Dict[str, float] = {
    "causal_structure": 2.0,
    "constraint": 1.5,
    "information_flow": 1.3,
    "search_landscape": 1.2,
    "recurrence": 1.0,
    "symmetry": 1.0,
    "hierarchy": 1.0,
    "periodicity": 0.8,
    "sparsity": 0.8,
    "graph_topology": 1.0,
}


def _as_dict(x: VectorLike, keys: Optional[Sequence[str]] = None) -> Dict[str, float]:
    if isinstance(x, StructuralFingerprint):
        d = {k: float(v) for k, v in x.features.items()}
    elif isinstance(x, Mapping):
        d = {str(k): float(v) for k, v in x.items()}
    else:
        seq = list(x)
        if keys is None:
            keys = [str(i) for i in range(len(seq))]
        d = {str(keys[i]): float(seq[i]) for i in range(len(seq))}
    return d


def _aligned(
    a: VectorLike, b: VectorLike
) -> Tuple[List[str], List[float], List[float]]:
    da, db = _as_dict(a), _as_dict(b)
    keys = sorted(set(da) | set(db))
    va = [da.get(k, 0.0) for k in keys]
    vb = [db.get(k, 0.0) for k in keys]
    return keys, va, vb


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def _mean(a: Sequence[float]) -> float:
    return sum(a) / len(a) if a else 0.0


def cosine_similarity(a: VectorLike, b: VectorLike) -> float:
    _, va, vb = _aligned(a, b)
    na, nb = _norm(va), _norm(vb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(-1.0, min(1.0, _dot(va, vb) / (na * nb)))


def cosine_distance(a: VectorLike, b: VectorLike) -> float:
    return 1.0 - cosine_similarity(a, b)


def l1_distance(a: VectorLike, b: VectorLike) -> float:
    keys, va, vb = _aligned(a, b)
    if not keys:
        return 0.0
    return sum(abs(x - y) for x, y in zip(va, vb)) / len(keys)


def l2_distance(a: VectorLike, b: VectorLike) -> float:
    keys, va, vb = _aligned(a, b)
    if not keys:
        return 0.0
    s = sum((x - y) ** 2 for x, y in zip(va, vb))
    return math.sqrt(s) / math.sqrt(len(keys))


def chebyshev_distance(a: VectorLike, b: VectorLike) -> float:
    keys, va, vb = _aligned(a, b)
    if not keys:
        return 0.0
    return max(abs(x - y) for x, y in zip(va, vb))


def correlation_similarity(a: VectorLike, b: VectorLike) -> float:
    _, va, vb = _aligned(a, b)
    n = len(va)
    if n < 2:
        return 0.0
    ma, mb = _mean(va), _mean(vb)
    ca = [x - ma for x in va]
    cb = [y - mb for y in vb]
    na, nb = _norm(ca), _norm(cb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(-1.0, min(1.0, _dot(ca, cb) / (na * nb)))


def weighted_l1_distance(
    a: VectorLike,
    b: VectorLike,
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    wmap = dict(DEFAULT_WEIGHTS)
    if weights:
        wmap.update({str(k): float(v) for k, v in weights.items()})
    keys, va, vb = _aligned(a, b)
    if not keys:
        return 0.0
    num = 0.0
    den = 0.0
    for k, x, y in zip(keys, va, vb):
        w = float(wmap.get(k, 1.0))
        num += w * abs(x - y)
        den += w
    return num / den if den else 0.0


def mahalanobis_distance(
    a: VectorLike,
    b: VectorLike,
    inv_cov: Optional[Sequence[Sequence[float]]] = None,
) -> float:
    keys, va, vb = _aligned(a, b)
    d = len(keys)
    if d == 0:
        return 0.0
    diff = [x - y for x, y in zip(va, vb)]
    if inv_cov is None:
        return math.sqrt(sum(z * z for z in diff) / d)
    if len(inv_cov) != d or any(len(row) != d for row in inv_cov):
        raise ValueError("inv_cov must be d×d matching aligned feature keys")
    acc = 0.0
    for i in range(d):
        inner = sum(inv_cov[i][j] * diff[j] for j in range(d))
        acc += diff[i] * inner
    return math.sqrt(max(0.0, acc))


def similarity(
    a: VectorLike,
    b: VectorLike,
    metric: str = "l1",
    weights: Optional[Mapping[str, float]] = None,
    inv_cov: Optional[Sequence[Sequence[float]]] = None,
) -> float:
    m = metric.lower().strip()
    if m == "cosine":
        return 0.5 * (cosine_similarity(a, b) + 1.0)
    if m == "correlation":
        return 0.5 * (correlation_similarity(a, b) + 1.0)
    if m == "l1":
        return max(0.0, 1.0 - l1_distance(a, b))
    if m == "l2":
        return max(0.0, 1.0 - l2_distance(a, b))
    if m == "chebyshev":
        return max(0.0, 1.0 - chebyshev_distance(a, b))
    if m == "weighted_l1":
        return max(0.0, 1.0 - weighted_l1_distance(a, b, weights=weights))
    if m == "mahalanobis":
        d = mahalanobis_distance(a, b, inv_cov=inv_cov)
        return max(0.0, 1.0 - min(1.0, d))
    raise ValueError(f"unknown metric: {metric}")


def distance(
    a: VectorLike,
    b: VectorLike,
    metric: str = "l1",
    weights: Optional[Mapping[str, float]] = None,
    inv_cov: Optional[Sequence[Sequence[float]]] = None,
) -> float:
    return 1.0 - similarity(a, b, metric=metric, weights=weights, inv_cov=inv_cov)


@dataclass
class MechanismGraph:
    """Simple directed labeled graph for mechanism structure."""

    nodes: List[str] = field(default_factory=list)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)

    def normalized(self) -> "MechanismGraph":
        nodes = sorted(set(self.nodes) | {u for u, v, _ in self.edges} | {v for u, v, _ in self.edges})
        edges = sorted(set((str(u), str(v), str(lab)) for u, v, lab in self.edges))
        return MechanismGraph(nodes=nodes, edges=edges)


def graph_edit_distance(
    g1: MechanismGraph,
    g2: MechanismGraph,
    node_sub_cost: float = 1.0,
    edge_sub_cost: float = 1.0,
    insert_delete_cost: float = 1.0,
) -> float:
    """Approximate GED for small labeled digraphs."""
    a = g1.normalized()
    b = g2.normalized()
    na, nb = a.nodes, b.nodes

    def sig(graph: MechanismGraph, node: str) -> set:
        s = set()
        for u, v, lab in graph.edges:
            if u == node:
                s.add(f"out:{lab}:{v}")
            if v == node:
                s.add(f"in:{lab}:{u}")
        return s

    unmatched_a = set(na)
    unmatched_b = set(nb)
    pairs: List[Tuple[str, str]] = []
    for n in list(unmatched_a):
        if n in unmatched_b:
            pairs.append((n, n))
            unmatched_a.discard(n)
            unmatched_b.discard(n)

    def jaccard(x: set, y: set) -> float:
        if not x and not y:
            return 1.0
        if not x or not y:
            return 0.0
        return len(x & y) / len(x | y)

    residual = []
    for u in list(unmatched_a):
        best_v, best_s = None, -1.0
        su = sig(a, u)
        for v in unmatched_b:
            s = jaccard(su, sig(b, v))
            if s > best_s:
                best_s, best_v = s, v
        if best_v is not None:
            residual.append((u, best_v, best_s))
    residual.sort(key=lambda t: t[2], reverse=True)
    used_b = set()
    for u, v, s in residual:
        if u in unmatched_a and v in unmatched_b and v not in used_b:
            pairs.append((u, v))
            unmatched_a.discard(u)
            unmatched_b.discard(v)
            used_b.add(v)

    cost = insert_delete_cost * (len(unmatched_a) + len(unmatched_b))
    for u, v in pairs:
        if u != v:
            cost += node_sub_cost

    mapping = {u: v for u, v in pairs}

    def map_edges(graph: MechanismGraph, forward: bool) -> set:
        out = set()
        for u, v, lab in graph.edges:
            if forward:
                mu, mv = mapping.get(u), mapping.get(v)
            else:
                inv = {y: x for x, y in mapping.items()}
                mu, mv = inv.get(u), inv.get(v)
            if mu is None or mv is None:
                continue
            out.add((mu, mv, lab))
        return out

    ea = map_edges(a, forward=True)
    eb = set((u, v, lab) for u, v, lab in b.edges)
    matched_b = set(mapping.values())
    ea = {e for e in ea if e[0] in matched_b and e[1] in matched_b}
    eb = {e for e in eb if e[0] in matched_b and e[1] in matched_b}

    only_a = ea - eb
    only_b = eb - ea
    subs = 0
    used = set()
    for u, v, lab in list(only_a):
        for u2, v2, lab2 in list(only_b):
            if (u2, v2, lab2) in used:
                continue
            if u == u2 and v == v2 and lab != lab2:
                subs += 1
                used.add((u2, v2, lab2))
                only_a.discard((u, v, lab))
                break
    only_b = {e for e in only_b if e not in used}
    cost += edge_sub_cost * subs
    cost += insert_delete_cost * (len(only_a) + len(only_b))

    denom = max(1, len(na) + len(nb) + len(a.edges) + len(b.edges))
    return cost / denom


def graph_similarity(g1: MechanismGraph, g2: MechanismGraph) -> float:
    d = graph_edit_distance(g1, g2)
    return max(0.0, 1.0 - min(1.0, d))


def fingerprint_similarity(
    a: StructuralFingerprint,
    b: StructuralFingerprint,
    metric: str = "weighted_l1",
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    return similarity(a, b, metric=metric, weights=weights)


def fingerprint_distance(
    a: StructuralFingerprint,
    b: StructuralFingerprint,
    metric: str = "weighted_l1",
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    return distance(a, b, metric=metric, weights=weights)
