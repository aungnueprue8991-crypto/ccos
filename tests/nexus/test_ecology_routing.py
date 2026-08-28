"""Event-driven ecology: anomaly rule, workspace, hooks."""

from __future__ import annotations

from nexus.routing.ecology import CognitiveEcology
from nexus.routing.hooks import ValidationHooks
from nexus.routing.rules import ActivationRules, Observation, anomaly_score
from nexus.workspace.blackboard import CognitiveState, GlobalWorkspace
from nexus.workspace.events import CogEvent, CogEventType


def test_anomaly_score_increases_with_error():
    state = CognitiveState(uncertainty=0.5)
    low = Observation("a", 0.0, 0.1, 0.9, 0.2)
    high = Observation("b", 0.0, 1.0, 0.3, 0.9)
    assert anomaly_score(high, state) > anomaly_score(low, state)


def test_anomaly_rule_emits_above_threshold():
    rules = ActivationRules(anomaly_threshold=0.5)
    state = CognitiveState(uncertainty=0.7)
    obs = Observation("x", 0.0, 1.0, 0.3, 0.9, entity="thermal")
    events = rules.anomaly_rule(obs, state)
    assert events
    types = {e.type for e in events}
    assert CogEventType.ANOMALY.value in types
    assert CogEventType.ENGINE_WAKE.value in types
    assert "question_engine" in events[0].targets


def test_anomaly_rule_silent_below_threshold():
    rules = ActivationRules(anomaly_threshold=0.99)
    state = CognitiveState(uncertainty=0.1)
    obs = Observation("x", 0.5, 0.51, 0.95, 0.1)
    assert rules.anomaly_rule(obs, state) == []


def test_workspace_broadcast():
    ws = GlobalWorkspace()
    ev = CogEvent(type=CogEventType.ANOMALY.value, payload={"score": 0.8}, targets=["q"])
    ws.broadcast(ev, ["question_engine", "pattern_engine"])
    assert ws.anomalies
    assert "question_engine" in ws.attention
    assert ws.event_log


def test_pre_activation_blocks_no_budget():
    hooks = ValidationHooks()
    ev = CogEvent(type="x", payload={}, priority=0.5)
    r = hooks.pre_activation(ev, budget=0.0)
    assert r.passed is False


def test_validate_anomaly_downstream():
    hooks = ValidationHooks()
    out = hooks.validate_anomaly_event(
        {"type": "anomaly.detected"},
        {"engines": ["question_engine"], "memory_queried": True},
    )
    assert out["event_emitted"] is True
    assert out["question_was_woken"] is True


def test_ecology_anomaly_to_discovery():
    eco = CognitiveEcology(anomaly_threshold=0.4, run_world=True, seed=42)
    result = eco.run_anomaly_to_discovery(
        predicted=0.0, actual=1.0, confidence=0.3, salience=0.9
    )
    assert result.event_count >= 3
    phases = [s.phase for s in result.steps]
    assert "anomaly_broadcast" in phases
    assert result.evidence_verdict in ("support", "falsify", "inconclusive")
    assert result.discovery == "thermal_equilibration_confirmed"
    assert result.evidence_verdict == "support"
    assert result.hook_pass_rate >= 0.5
