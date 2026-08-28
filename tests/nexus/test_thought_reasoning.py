"""Thought Engine, Reasoning Engine, Heart, concept, theory competition."""

from __future__ import annotations

from pathlib import Path
import tempfile

from nexus.heart.attention import CognitiveHeart
from nexus.hypothesis.evolution import HypothesisEvolution
from nexus.orchestration.cognitive_loop import CognitiveOrchestrator
from nexus.reasoning.engine import ReasoningEngine
from nexus.serendipity.engine import SerendipityEngine
from nexus.theory.competition import TheoryCompetition
from nexus.thought.engine import ThoughtEngine
from nexus.types import Hypothesis, ThoughtKind


def test_thought_engine_generates_kinds():
    te = ThoughtEngine(seed=1)
    thoughts = te.generate("thermal anomaly", domain="thermodynamics", anomalies=["T≠pred"], n=5)
    assert len(thoughts) >= 3
    kinds = {t.kind for t in thoughts}
    assert ThoughtKind.COUNTERFACTUAL in kinds or ThoughtKind.ASSOCIATION in kinds


def test_reasoning_from_thoughts():
    te = ThoughtEngine(seed=2)
    thoughts = te.generate("focus", domain="physics", n=3)
    re = ReasoningEngine()
    results = re.process(thoughts)
    assert results
    assert results[0].conclusion
    assert results[0].falsifiers


def test_heart_focus():
    heart = CognitiveHeart()
    obj, items = heart.evaluate_focus(
        prediction_errors=[{"entity": "x", "surprise": 0.9, "predicted": 1, "actual": 0}],
        domain="thermo",
    )
    assert obj.priority > 0.3
    assert items
    assert items[0].score >= items[-1].score


def test_theory_competition_updates():
    tc = TheoryCompetition()
    ts = tc.seed_competitors(["A causes B", "C confounds", "A ↔ B"])
    lik = {ts[0].theory_id: 0.9, ts[1].theory_id: 0.2, ts[2].theory_id: 0.3}
    tc.update_from_observation(lik)
    assert tc.best() is not None
    assert tc.best().theory_id == ts[0].theory_id


def test_hypothesis_evolution():
    evo = HypothesisEvolution()
    h = Hypothesis(statement="WD helps exploration", confidence=0.5, predictions={"gain": True})
    h2 = evo.evolve(h, "mixed", boundary_hint="low noise")
    assert "low noise" in h2.statement
    assert h2.status == "proposed"


def test_serendipity_budget():
    eng = SerendipityEngine(
        seed=0, base_budget=1.0, tokens_per_epoch=5, structural_tau=0.2, min_lexical_distance=0.1
    )
    out = []
    for _ in range(15):
        out = eng.maybe_link(
            ["thermal_flow_equilibrium", "resource_equalization_constraint"],
            domain="x",
            novelty_hunger=1.0,
            resource_pressure=0.0,
        )
        if out:
            break
    assert out and out[0].kind == ThoughtKind.SERENDIPITY


def test_full_cycle_thought_reasoning_ledger():
    path = Path(tempfile.mkdtemp()) / "tr.db"
    orch = CognitiveOrchestrator(seed=42, ledger_path=path, strict_world=True)
    r = orch.run_cycle()
    assert r.thoughts, "expected thought stream"
    assert r.reasoning, "expected reasoning results"
    assert r.oracle_accepted is True
    assert r.event_ledger_chain_ok is True
    types = [e.get("type") for e in r.ledger_events]
    assert "cognitive_heart" in types
    assert "thought" in types
    assert "reasoning" in types
    assert r.concepts, "expected concept formation after discovery"
    assert r.theory_ranking or r.hypotheses
