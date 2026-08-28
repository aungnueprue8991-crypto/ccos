"""Cognitive Ecology runner — event-driven anomaly→discovery control loop.

Not a linear pipeline: rules publish to GlobalWorkspace; handlers wake engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from nexus.routing.hooks import ValidationHooks
from nexus.routing.rules import ActivationRules, Observation
from nexus.workspace.blackboard import GlobalWorkspace
from nexus.workspace.events import CogEvent, CogEventType


@dataclass
class EcologyStepResult:
    phase: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    woken: List[str] = field(default_factory=list)
    hooks: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class EcologyRunResult:
    steps: List[EcologyStepResult]
    final_state: Dict[str, float]
    discovery: Optional[str]
    evidence_verdict: Optional[str]
    event_count: int
    hook_pass_rate: float


class CognitiveEcology:
    """Self-organizing loop over GlobalWorkspace + activation rules."""

    def __init__(
        self,
        anomaly_threshold: float = 0.55,
        run_world: bool = True,
        seed: int = 42,
    ):
        self.ws = GlobalWorkspace()
        self.rules = ActivationRules(anomaly_threshold=anomaly_threshold)
        self.hooks = ValidationHooks()
        self.run_world = run_world
        self.seed = seed
        self.budget = 1.0
        self._seen: set = set()
        self.downstream: Dict[str, Any] = {}

    def _accept(self, event: CogEvent) -> bool:
        pre = self.hooks.pre_activation(event, budget=self.budget, seen_ids=self._seen)
        if not pre.passed:
            return False
        self._seen.add(event.event_id)
        self.budget = max(0.0, self.budget - 0.05)
        return True

    def step_anomaly(self, obs: Observation) -> EcologyStepResult:
        events = self.rules.apply_anomaly_to_workspace(self.ws, obs)
        accepted = []
        woken = []
        hook_rows = []
        for ev in events:
            if not self._accept(ev):
                continue
            accepted.append(ev.to_dict())
            woken.extend(ev.targets or ev.payload.get("engines", []))
        woken = list(dict.fromkeys(woken))
        self.downstream = {
            "question_engine": "question_engine" in woken,
            "pattern_engine": "pattern_engine" in woken,
            "memory_queried": "memory_service" in woken,
            "engines": woken,
        }
        for ev in events:
            if ev.type == CogEventType.ANOMALY.value:
                post = self.hooks.post_activation(ev, self.downstream)
                hook_rows.append(post.details)
                val = self.hooks.validate_anomaly_event(ev.to_dict(), self.downstream)
                hook_rows.append(val)
        return EcologyStepResult(
            phase="anomaly_broadcast",
            events=accepted,
            woken=woken,
            hooks=hook_rows,
            notes=[f"anomaly score path for {obs.id}"],
        )

    def step_thought_question(self) -> EcologyStepResult:
        from nexus.thought.engine import ThoughtEngine
        from nexus.questions.generator import QuestionEngine
        from nexus.types import CognitiveObjective, DriveName

        te = ThoughtEngine(seed=self.seed)
        anoms = [a.get("entity", "x") for a in self.ws.anomalies]
        thoughts = te.generate(
            focus_description=anoms[0] if anoms else "anomaly",
            domain="thermodynamics",
            anomalies=anoms,
            n=4,
        )
        for t in thoughts:
            ev = CogEvent(
                type=CogEventType.THOUGHT.value,
                payload=t.to_dict(),
                source="thought_engine",
                targets=["reasoning_engine", "question_engine"],
            )
            if self._accept(ev):
                self.ws.publish(ev)

        qe = QuestionEngine()
        obj = CognitiveObjective(
            primary_drive=DriveName.SURPRISE,
            description="anomaly follow-up",
            domain="thermodynamics",
        )
        errors = []
        for a in self.ws.anomalies[:3]:
            errors.append(
                {
                    "entity": a.get("entity", "sys"),
                    "predicted": "stable",
                    "actual": "changed",
                    "surprise": float(a.get("score", 0.6)),
                }
            )
        qs = qe.from_objective(obj, prediction_errors=errors, domain="thermodynamics")
        for q in qs[:2]:
            ev = CogEvent(
                type=CogEventType.QUESTION.value,
                payload={"text": q.text, "kind": q.kind.value, "id": q.question_id},
                source="question_engine",
            )
            if self._accept(ev):
                self.ws.publish(ev)

        self.downstream["new_question"] = bool(qs)
        self.downstream["hypothesis_updated"] = False
        return EcologyStepResult(
            phase="thought_question",
            events=[e.to_dict() for e in self.ws.event_log if e.type in (
                CogEventType.THOUGHT.value, CogEventType.QUESTION.value
            )][-10:],
            woken=["thought_engine", "question_engine"],
            notes=[f"{len(thoughts)} thoughts, {len(qs)} questions"],
        )

    def step_hypothesis_competition(self) -> EcologyStepResult:
        from nexus.reasoning.engine import ReasoningEngine
        from nexus.theory.competition import TheoryCompetition
        from nexus.types import Thought

        thoughts = []
        for t in self.ws.thoughts[-5:]:
            thoughts.append(
                Thought(
                    kind=t.get("kind", "association"),
                    content=t.get("content", ""),
                    salience=float(t.get("salience", 0.5)),
                )
            )
        if not thoughts:
            return EcologyStepResult(phase="hypothesis", notes=["no thoughts"])

        reasoned = ReasoningEngine().process(thoughts, domain="thermodynamics")
        statements = [r.conclusion[:120] for r in reasoned[:3]]
        preds = [r.predictions for r in reasoned[:3]]
        tc = TheoryCompetition()
        theories = tc.seed_competitors(statements, preds)
        lik = {t.theory_id: 0.4 + 0.2 * i for i, t in enumerate(theories)}
        tc.update_from_observation(lik)
        ranking = [
            {"statement": t.statement[:80], "posterior": round(t.posterior, 4)}
            for t in tc.ranking()
        ]
        ev = CogEvent(
            type=CogEventType.THEORY_COMPETE.value,
            payload={"ranking": ranking},
            source="theory_competition",
        )
        if self._accept(ev):
            self.ws.publish(ev)
        for r in reasoned:
            hev = CogEvent(
                type=CogEventType.HYPOTHESIS.value,
                payload={
                    "statement": r.conclusion[:120],
                    "confidence": r.confidence,
                    "falsifiers": r.falsifiers,
                },
                source="hypothesis_engine",
            )
            if self._accept(hev):
                self.ws.publish(hev)
        self.downstream["hypothesis_updated"] = True
        return EcologyStepResult(
            phase="hypothesis_competition",
            events=[ev.to_dict()],
            woken=["hypothesis_engine", "theory_competition"],
            notes=[f"{len(ranking)} competing theories"],
        )

    def step_experiment_evidence(self) -> EcologyStepResult:
        discovery = None
        verdict = "inconclusive"
        notes = []
        if self.run_world:
            try:
                from world.governance.bridge import StrictCCOSClient
                from world.science.loop import ScientificCivilizationLoop

                client = StrictCCOSClient()
                loop = ScientificCivilizationLoop(
                    seed=self.seed, strict=True, ccos=client
                )
                result = loop.run_thermodynamics_experiment(agent_id="ecology-sci")
                oracle = any(
                    e.get("type") == "oracle_verdict" and e.get("accepted")
                    for e in result.ledger_events
                )
                if result.success and oracle:
                    discovery = result.discovery
                    verdict = "support"
                elif result.success:
                    verdict = "inconclusive"
                else:
                    verdict = "falsify"
                notes.append(f"world success={result.success} oracle={oracle}")
            except Exception as e:
                notes.append(f"world error: {e}")
                verdict = "inconclusive"

        etype = {
            "support": CogEventType.SUPPORT.value,
            "falsify": CogEventType.FALSIFY.value,
            "inconclusive": CogEventType.INCONCLUSIVE.value,
        }[verdict]
        ev = CogEvent(
            type=etype,
            payload={"discovery": discovery, "verdict": verdict},
            source="evidence_gate",
        )
        if self._accept(ev):
            self.ws.publish(ev)

        if verdict == "support" and discovery:
            for t in ("abstraction.extracted", "transfer.proposed"):
                e2 = CogEvent(
                    type=t,
                    payload={"mechanism": discovery},
                    source="post_evidence",
                )
                if self._accept(e2):
                    self.ws.publish(e2)

        cal = self.hooks.calibration(0.65, verdict == "support")
        return EcologyStepResult(
            phase="experiment_evidence",
            events=[ev.to_dict()],
            woken=["experiment_manager", "evidence_gate"],
            hooks=[cal.details],
            notes=notes + [f"verdict={verdict}", f"discovery={discovery}"],
        )

    def run_anomaly_to_discovery(
        self,
        predicted: float = 0.0,
        actual: float = 1.0,
        confidence: float = 0.4,
        salience: float = 0.8,
    ) -> EcologyRunResult:
        obs = Observation(
            id="obs-thermal-1",
            predicted_value=predicted,
            actual_value=actual,
            prediction_confidence=confidence,
            salience=salience,
            entity="thermal_system",
            domain="thermodynamics",
        )
        steps = [
            self.step_anomaly(obs),
            self.step_thought_question(),
            self.step_hypothesis_competition(),
            self.step_experiment_evidence(),
        ]
        discovery = None
        verdict = None
        for s in steps:
            for n in s.notes:
                if n.startswith("discovery="):
                    discovery = n.split("=", 1)[1]
                    if discovery == "None":
                        discovery = None
            for e in s.events:
                if e.get("payload", {}).get("verdict"):
                    verdict = e["payload"]["verdict"]
                if e.get("payload", {}).get("discovery"):
                    discovery = e["payload"]["discovery"]

        hist = self.hooks.history
        if hist:
            rate = sum(1 for h in hist if h.get("passed", True)) / len(hist)
        else:
            rate = 1.0

        return EcologyRunResult(
            steps=steps,
            final_state=self.ws.state.as_dict(),
            discovery=discovery,
            evidence_verdict=verdict,
            event_count=len(self.ws.event_log),
            hook_pass_rate=rate,
        )
