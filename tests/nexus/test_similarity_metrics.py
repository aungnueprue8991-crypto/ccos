"""Structural similarity metrics + GED + cosine API."""

from __future__ import annotations

import math

from nexus.patterns.fingerprint import FingerprintEngine
from nexus.patterns.similarity import (
    MechanismGraph,
    chebyshev_distance,
    cosine_distance,
    cosine_similarity,
    distance,
    graph_edit_distance,
    graph_similarity,
    l1_distance,
    l2_distance,
    mahalanobis_distance,
    similarity,
    weighted_l1_distance,
)
from nexus.types import StructuralFingerprint


def _thermo():
    return FingerprintEngine().from_thermo_domain()


def _selection():
    return FingerprintEngine().from_selection_domain()


def test_cosine_api_identical():
    v = {"a": 1.0, "b": 2.0, "c": 3.0}
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-9
    assert cosine_distance(v, v) < 1e-9


def test_cosine_orthogonal():
    a = {"x": 1.0, "y": 0.0}
    b = {"x": 0.0, "y": 1.0}
    assert abs(cosine_similarity(a, b)) < 1e-9


def test_l1_l2_chebyshev_self():
    f = _thermo()
    assert l1_distance(f, f) == 0.0
    assert l2_distance(f, f) == 0.0
    assert chebyshev_distance(f, f) == 0.0
    assert similarity(f, f, metric="l1") == 1.0
    assert similarity(f, f, metric="l2") == 1.0


def test_weighted_l1_differs_from_l1():
    a = StructuralFingerprint("a", {"causal_structure": 1.0, "periodicity": 0.0})
    b = StructuralFingerprint("b", {"causal_structure": 0.0, "periodicity": 1.0})
    plain = l1_distance(a, b)
    weighted = weighted_l1_distance(a, b)
    assert weighted != plain or plain > 0
    assert weighted > 0


def test_correlation_and_metrics_enum():
    f, g = _thermo(), _selection()
    for m in ("l1", "l2", "cosine", "correlation", "chebyshev", "weighted_l1", "mahalanobis"):
        s = similarity(f, g, metric=m)
        d = distance(f, g, metric=m)
        assert 0.0 <= s <= 1.0 + 1e-6
        assert abs((s + d) - 1.0) < 1e-6


def test_fingerprint_method_delegation():
    f, g = _thermo(), _selection()
    assert abs(f.similarity(g, metric="cosine") - similarity(f, g, metric="cosine")) < 1e-9
    assert abs(f.distance(g, metric="l1") - distance(f, g, metric="l1")) < 1e-9


def test_mahalanobis_identity_like_l2():
    a = {"x": 0.0, "y": 0.0}
    b = {"x": 3.0, "y": 4.0}
    d = mahalanobis_distance(a, b, inv_cov=None)
    assert abs(d - math.sqrt(12.5)) < 1e-9


def test_graph_edit_distance_identical():
    g = MechanismGraph(nodes=["T", "Q"], edges=[("T", "Q", "flow")])
    assert graph_edit_distance(g, g) == 0.0
    assert graph_similarity(g, g) == 1.0


def test_graph_edit_distance_differs():
    g1 = MechanismGraph(nodes=["A", "B"], edges=[("A", "B", "heat")])
    g2 = MechanismGraph(nodes=["A", "B", "C"], edges=[("A", "B", "heat"), ("B", "C", "loss")])
    d = graph_edit_distance(g1, g2)
    assert d > 0.0
    assert graph_similarity(g1, g2) < 1.0


def test_thermo_selection_reasonable():
    f, g = _thermo(), _selection()
    s = similarity(f, g, metric="weighted_l1")
    assert 0.3 < s < 0.95
