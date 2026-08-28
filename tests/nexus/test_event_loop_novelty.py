"""Event-loop ecology, novelty engine, MAP-Elites."""

from __future__ import annotations

from nexus.evolution.map_elites import CognitiveMapElites
from nexus.novelty.engine import NoveltyEngine
from nexus.routing.loop import EcologyEventLoop


def test_novelty_wording_not_enough():
    eng = NoveltyEngine()
    s = eng.score(
        "the quick brown fox",
        known_texts=["the quick brown fox jumps"],
        has_new_prediction=False,
        structural_sim_to_known=0.9,
        mechanism="same",
    )
    s2 = eng.score(
        "entirely new mechanism of periodic adaptive compression",
        known_texts=["old text"],
        mechanism="periodic_adaptive_compression",
        has_new_prediction=True,
        structural_sim_to_known=0.2,
        other_domain="biology",
        domain="algorithms",
    )
    assert s2.genuine_idea() is True
    assert s2.mechanistic >= 0.5 or s2.predictive >= 0.5


def test_map_elites_archive():
    me = CognitiveMapElites()
    assert me.best() is not None
    cell = me.select_for_state(uncertainty=0.9, novelty_pressure=0.8)
    assert cell.pipeline
    me.observe_outcome(cell, success=True, transfer=True)
    assert me.coverage() > 0


def test_event_loop_anomaly_discovery():
    loop = EcologyEventLoop(seed=42, max_steps=35)
    n = loop.inject_anomaly(predicted=0.0, actual=1.0, confidence=0.25, salience=0.9)
    assert n >= 1
    types = [e.type for e in loop.ws.event_log]
    assert any("anomaly" in t for t in types)
    assert any("thought" in t for t in types)
    assert any(
        x in t
        for t in types
        for x in ("hypothesis", "theory", "experiment", "support", "evidence")
    )
    assert any(t.endswith("support") or "support" in t for t in types)
