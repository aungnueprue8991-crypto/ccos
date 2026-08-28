"""True event-loop ecology — handler registry + priority broadcast queue.

Engines register handlers; the loop dispatches until budget/idle.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from nexus.evolution.map_elites import CognitiveMapElites
from nexus.novelty.engine import NoveltyEngine
from nexus.routing.hooks import ValidationHooks
from nexus.routing.rules import ActivationRules, Observation
from nexus.workspace.blackboard import GlobalWorkspace
from nexus.workspace.events import CogEvent, CogEventType
from nexus.dream.engine import DreamEngine
from nexus.evolution.cognitive import CognitiveEvolution
from nexus.metacognition.policy import RoutingPolicy
from nexus.memory.hybrid import HybridMemory, MemoryEntry
from nexus.perception.binding import BindingEngine, RawModality
from nexus.perception.observation import ObservationEngine
from nexus.perception.salience import SalienceEngine

Handler = Callable[[CogEvent, GlobalWorkspace], List[CogEvent]]


@dataclass(order=True)
class _PQItem:
    neg_priority: float
    seq: int
    event: CogEvent = field(compare=False)


class EcologyEventLoop:
    """Self-organizing dispatch: events → handlers → more events."""

    def __init__(self, seed: int = 42, max_steps: int = 40):
        self.ws = GlobalWorkspace()
        self.rules = ActivationRules()
        self.hooks = ValidationHooks()
        self.novelty = NoveltyEngine()
        self.map_elites = CognitiveMapElites()
        self.evolution = CognitiveEvolution(seed=seed)
        self.dream = DreamEngine(seed=seed + 1)
        self.policy = RoutingPolicy()
        self.memory = HybridMemory()
        self.binding = BindingEngine()
        self.observation = ObservationEngine()
        self.salience = SalienceEngine()
        self.seed = seed
        self.episodes: list = []
        self.concepts: list = []
        self.max_steps = max_steps
        self.budget = 1.0
        self._seq = 0
        self._queue: List[_PQItem] = []
        self._handlers: Dict[str, List[Handler]] = {}
        self._seen: set = set()
        self.log: List[Dict[str, Any]] = []
        self._register_builtins()

    def register(self, event_prefix: str, handler: Handler) -> None:
        self._handlers.setdefault(event_prefix, []).append(handler)

    def submit(self, event: CogEvent) -> None:
        pre = self.hooks.pre_activation(event, budget=self.budget, seen_ids=self._seen)
        if not pre.passed:
            self.log.append({"action": "reject", "type": event.type, **pre.details})
            return
        self._seen.add(event.event_id)
        self._seq += 1
        heapq.heappush(
            self._queue,
            _PQItem(neg_priority=-event.priority, seq=self._seq, event=event),
        )

    def _handlers_for(self, event_type: str) -> List[Handler]:
        out: List[Handler] = []
        for prefix, hs in self._handlers.items():
            if event_type == prefix or event_type.startswith(prefix.rstrip("*")):
                out.extend(hs)
        return out

    def tick(self) -> Optional[CogEvent]:
        if not self._queue or self.budget <= 0:
            return None
        item = heapq.heappop(self._queue)
        event = item.event
        self.ws.publish(event)
        self.budget = max(0.0, self.budget - 0.04)
        for h in self._handlers_for(event.type):
            try:
                children = h(event, self.ws) or []
            except Exception as e:
                self.log.append({"action": "handler_error", "error": str(e), "type": event.type})
                continue
            for ch in children:
                ch.parent_id = event.event_id
                self.submit(ch)
        self.log.append({"action": "dispatch", "type": event.type, "targets": event.targets})
        return event

    def run_until_idle(self) -> int:
        n = 0
        while n < self.max_steps:
            if self.tick() is None:
                break
            n += 1
        return n

    def inject_anomaly(
        self,
        predicted: float = 0.0,
        actual: float = 1.0,
        confidence: float = 0.3,
        salience: float = 0.85,
        text: str = "thermal system prediction mismatch",
    ) -> int:
        percept = self.binding.bind([
            RawModality("text", text, confidence=0.9),
            RawModality("environment", {"entity": "thermal_system"}, confidence=0.8),
        ])
        sobs = self.observation.normalize(
            percept, domain="thermodynamics",
            predicted=predicted, actual=actual, prediction_confidence=confidence,
        )
        sal = self.salience.score(sobs, state_uncertainty=self.ws.state.uncertainty)
        self.ws.publish(self.observation.to_event(sobs))
        self.memory.write(MemoryEntry(
            type="episodic", content=sobs.text, domain="thermodynamics",
            confidence=confidence, tags=["anomaly", "thermal"],
            novelty_score=sal.novelty, provenance=list(sobs.provenance),
        ))
        obs = Observation(
            id=sobs.observation_id,
            predicted_value=predicted,
            actual_value=actual,
            prediction_confidence=confidence,
            salience=max(salience, sal.aggregate),
            entity="thermal_system",
            domain="thermodynamics",
        )
        for ev in self.rules.anomaly_rule(obs, self.ws.state):
            self.submit(ev)
        self.ws.update_state(
            surprise=min(1.0, abs(actual - predicted)),
            uncertainty=min(1.0, self.ws.state.uncertainty + 0.15),
            curiosity=min(1.0, self.ws.state.curiosity + 0.2),
        )
        return self.run_until_idle()

    def _register_builtins(self) -> None:
        def on_anomaly(event: CogEvent, ws: GlobalWorkspace) -> List[CogEvent]:
            from nexus.thought.engine import ThoughtEngine
            from nexus.questions.generator import QuestionEngine
            from nexus.types import CognitiveObjective, DriveName

            te = ThoughtEngine(seed=self.seed)
            thoughts = te.generate(
                focus_description=str(event.payload.get("entity", "anomaly")),
                domain=str(event.payload.get("domain", "general")),
                anomalies=[str(event.payload.get("entity", "x"))],
                n=3,
            )
            out: List[CogEvent] = []
            for t in thoughts:
                out.append(
                    CogEvent(
                        type=CogEventType.THOUGHT.value,
                        payload=t.to_dict(),
                        source="thought_engine",
                        priority=0.55 + 0.1 * t.novelty,
                        targets=["reasoning_engine", "question_engine"],
                    )
                )
            out.append(
                CogEvent(
                    type=CogEventType.QUESTION.value,
                    payload={
                        "text": (
                            f"Why frame this as predicted≠actual for "
                            f"{event.payload.get('entity')}? Alternative representations?"
                        ),
                        "kind": "question_about_question",
                    },
                    source="question_about_question",
                    priority=0.7,
                    targets=["thought_engine", "reasoning_engine"],
                )
            )
            qe = QuestionEngine()
            obj = CognitiveObjective(
                primary_drive=DriveName.SURPRISE,
                description="anomaly",
                domain=str(event.payload.get("domain", "general")),
            )
            errors = [{
                "entity": event.payload.get("entity", "sys"),
                "predicted": "stable",
                "actual": "changed",
                "surprise": float(event.payload.get("score", 0.6)),
            }]
            for q in qe.from_objective(obj, prediction_errors=errors)[:2]:
                out.append(
                    CogEvent(
                        type=CogEventType.QUESTION.value,
                        payload={"text": q.text, "kind": q.kind.value},
                        source="question_engine",
                        priority=0.6,
                    )
                )
            return out

        def on_thought(event: CogEvent, ws: GlobalWorkspace) -> List[CogEvent]:
            from nexus.reasoning.engine import ReasoningEngine
            from nexus.types import Thought

            t = Thought(
                content=str(event.payload.get("content", "")),
                kind=event.payload.get("kind", "association"),
                salience=float(event.payload.get("salience", 0.5)),
            )
            results = ReasoningEngine().process([t])
            out = []
            for r in results:
                nov = self.novelty.score(
                    r.conclusion,
                    known_texts=[x.get("content", "") for x in ws.thoughts[-10:]],
                    has_new_prediction=bool(r.predictions),
                    mechanism=r.method,
                )
                out.append(
                    CogEvent(
                        type=CogEventType.HYPOTHESIS.value,
                        payload={
                            "statement": r.conclusion[:160],
                            "confidence": r.confidence,
                            "falsifiers": r.falsifiers,
                            "novelty": nov.as_dict(),
                            "genuine_novelty": nov.genuine_idea(),
                        },
                        source="reasoning_engine",
                        priority=0.5 + 0.2 * r.confidence,
                    )
                )
            return out

        def on_hypothesis(event: CogEvent, ws: GlobalWorkspace) -> List[CogEvent]:
            if len(ws.hypotheses) < 2:
                return []
            return [
                CogEvent(
                    type=CogEventType.THEORY_COMPETE.value,
                    payload={"n": len(ws.hypotheses)},
                    source="activation",
                    priority=0.72,
                    targets=["theory_competition", "simulation_engine"],
                )
            ]

        def on_compete(event: CogEvent, ws: GlobalWorkspace) -> List[CogEvent]:
            from nexus.theory.competition import TheoryCompetition

            statements = [h.get("statement", "")[:120] for h in ws.hypotheses[-4:]]
            if len(statements) < 2:
                return []
            tc = TheoryCompetition()
            theories = tc.seed_competitors(statements)
            lik = {t.theory_id: 0.3 + 0.15 * i for i, t in enumerate(theories)}
            tc.update_from_observation(lik)
            ranking = [
                {"statement": t.statement[:80], "posterior": round(t.posterior, 4)}
                for t in tc.ranking()
            ]
            cell = self.map_elites.select_for_state(
                ws.state.uncertainty, ws.state.novelty_pressure
            )
            return [
                CogEvent(
                    type=CogEventType.EXPERIMENT.value,
                    payload={
                        "ranking": ranking,
                        "strategy": cell.name,
                        "pipeline": cell.pipeline,
                    },
                    source="theory_competition",
                    priority=0.8,
                    targets=["experiment_manager"],
                )
            ]

        def on_experiment(event: CogEvent, ws: GlobalWorkspace) -> List[CogEvent]:
            discovery = None
            verdict = "inconclusive"
            try:
                from world.governance.bridge import StrictCCOSClient
                from world.science.loop import ScientificCivilizationLoop

                loop = ScientificCivilizationLoop(
                    seed=self.seed, strict=True, ccos=StrictCCOSClient()
                )
                result = loop.run_thermodynamics_experiment(agent_id="loop-sci")
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
            except Exception as e:
                ws.publish(
                    CogEvent(
                        type="experiment.error",
                        payload={"error": str(e)},
                        source="experiment_manager",
                    )
                )
            cell = self.map_elites.select_for_state(
                ws.state.uncertainty, ws.state.novelty_pressure
            )
            self.map_elites.observe_outcome(cell, success=(verdict == "support"))
            et = {
                "support": CogEventType.SUPPORT.value,
                "falsify": CogEventType.FALSIFY.value,
                "inconclusive": CogEventType.INCONCLUSIVE.value,
            }[verdict]
            out = [
                CogEvent(
                    type=et,
                    payload={"discovery": discovery, "verdict": verdict},
                    source="evidence_gate",
                    priority=0.85,
                )
            ]
            if verdict == "support" and discovery:
                out.append(
                    CogEvent(
                        type=CogEventType.ABSTRACTION.value,
                        payload={"mechanism": discovery},
                        source="abstraction_engine",
                        priority=0.7,
                    )
                )
                out.append(
                    CogEvent(
                        type=CogEventType.TRANSFER.value,
                        payload={"mechanism": discovery, "target": "resource_equalization"},
                        source="transfer_engine",
                        priority=0.65,
                    )
                )
            used = ["thought_engine", "question_engine", "reasoning_engine", "experiment_manager"]
            self.policy.update(used, success=(verdict == "support"), state=ws.state.as_dict())
            genome = self.evolution.select(k=1)[0]
            self.evolution.observe(genome, success=(verdict == "support"))
            if verdict == "support" and discovery:
                self.episodes.append({"domain": "thermodynamics", "description": discovery, "outcome": "success"})
                self.concepts.append(discovery)
                report = self.dream.run(
                    self.episodes,
                    concepts=self.concepts,
                    domains=["thermodynamics", "selection", "resource_equalization"],
                    mechanisms=[discovery, "conservation", "selection"],
                )
                out.extend(self.dream.to_events(report))
                self.evolution.evolve_generation()
            return out

        self.register(CogEventType.ANOMALY.value, on_anomaly)
        self.register(CogEventType.THOUGHT.value, on_thought)
        self.register(CogEventType.HYPOTHESIS.value, on_hypothesis)
        self.register(CogEventType.THEORY_COMPETE.value, on_compete)
        self.register(CogEventType.EXPERIMENT.value, on_experiment)
        self.register(CogEventType.ENGINE_WAKE.value, on_anomaly)
