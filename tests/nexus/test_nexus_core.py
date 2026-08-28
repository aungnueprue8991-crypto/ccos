"""NEXUS core — drives, questions, MAD, orchestrator cycle."""

from __future__ import annotations

from nexus.drives.arbitration import DriveManager
from nexus.emergence.detector import EmergenceClaim, EmergenceDetector
from nexus.orchestration.cognitive_loop import CognitiveOrchestrator
from nexus.orchestration.mad_arena import MADArena
from nexus.questions.generator import QuestionEngine
from nexus.types import CognitiveObjective, DriveName, Hypothesis, QuestionKind


def test_drive_arbitration_surprise_wins():
    dm = DriveManager()
    obj = dm.evaluate(
        prediction_errors=[{"surprise": 0.95, "entity": "x", "predicted": 1, "actual": 0}],
        competence=0.4,
    )
    assert obj.primary_drive in (DriveName.SURPRISE, DriveName.CURIOSITY)
    assert obj.priority > 0.3


def test_question_engine_from_errors():
    qe = QuestionEngine()
    obj = CognitiveObjective(primary_drive=DriveName.SURPRISE, description="test")
    qs = qe.from_objective(
        obj,
        prediction_errors=[{"entity": "a", "predicted": 1, "actual": 2, "surprise": 0.8}],
    )
    assert qs
    assert qs[0].kind == QuestionKind.ANOMALY


def test_mad_rejects_empty_hypothesis():
    arena = MADArena()
    h = Hypothesis(statement="maybe something", predictions={}, falsifiers=[])
    v = arena.debate(h)
    assert v.advanced is False


def test_mad_advances_falsifiable():
    arena = MADArena()
    h = Hypothesis(
        statement="heat flow causes equalization because energy redistributes",
        predictions={"temps_converge": True},
        falsifiers=["temps remain divergent under contact"],
        confidence=0.6,
    )
    v = arena.debate(h)
    assert v.advanced is True


def test_orchestrator_cycle_thermo():
    orch = CognitiveOrchestrator(seed=42, use_world_loop=True)
    result = orch.run_cycle(domain="thermodynamics", run_world_experiment=True)
    assert result.objective is not None
    assert result.questions
    assert result.oracle_accepted is True
    assert result.discovery == "thermal_equilibration_confirmed"
    assert result.theory is not None
    assert result.transfer is not None
    assert "capability" in result.q
    assert any(e["type"] == "cognitive_heart" for e in result.ledger_events)


def test_emergence_strict_checklist():
    det = EmergenceDetector()
    weak = EmergenceClaim(name="x", not_hardcoded=True, measurable=True)
    assert det.evaluate(weak)["accepted"] is False
    strong = EmergenceClaim(
        name="periodic_abstraction",
        not_hardcoded=True,
        appears_through_interaction=True,
        measurable=True,
        transfers=True,
        survives_ablation=True,
        reproduces=True,
    )
    assert det.evaluate(strong)["accepted"] is True
