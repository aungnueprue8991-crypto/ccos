"""CCOS-NEXUS cognitive orchestrator — Heart → Thought → Reasoning → Evidence.

Thought generates possibilities. Reasoning tests them. Evidence decides knowledge.
CCOS EventLedger + strict world path remain underneath.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id

from nexus.abstraction.extractor import AbstractionEngine
from nexus.causality.models import CausalEngine
from nexus.concepts.formation import ConceptFormationEngine
from nexus.consolidation.sleep import ConsolidationEngine
from nexus.creativity.engine import CreativityEngine
from nexus.curriculum.generator import CurriculumEngine
from nexus.emergence.detector import EmergenceDetector
from nexus.heart.attention import CognitiveHeart
from nexus.hypothesis.evolution import HypothesisEvolution
from nexus.ideas.generator import IdeaEngine
from nexus.imagination.simulator import ImaginationEngine
from nexus.invention.builder import InventionEngine
from nexus.ledger_bridge import NexusLedgerBridge
from nexus.metacognition.self_model import MetaCognition
from nexus.orchestration.mad_arena import MADArena
from nexus.patterns.fingerprint import FingerprintEngine, PatternDiscoveryEngine
from nexus.questions.evaluator import QuestionEvaluator
from nexus.questions.generator import QuestionEngine
from nexus.reasoning.engine import ReasoningEngine
from nexus.serendipity.engine import SerendipityEngine
from nexus.theory.competition import TheoryCompetition
from nexus.thought.engine import ThoughtEngine
from nexus.transfer.hidden_domain import HiddenDomainBenchmark, HiddenDomainResult
from nexus.transfer.predictor import TransferEngine
from nexus.types import (
    CognitiveObjective,
    Hypothesis,
    IntelligenceVector,
    ResearchQuestion,
    StrategyGenome,
    Theory,
    Thought,
)


@dataclass
class CycleResult:
    objective: CognitiveObjective
    questions: List[ResearchQuestion]
    hypotheses: List[Hypothesis]
    arena_advanced: List[str]
    theory: Optional[Theory]
    transfer: Optional[Dict[str, Any]]
    artifact_id: Optional[str]
    oracle_accepted: Optional[bool]
    discovery: Optional[str]
    q: Dict[str, float]
    intelligence: Dict[str, float]
    notes: List[str] = field(default_factory=list)
    ledger_events: List[Dict[str, Any]] = field(default_factory=list)
    event_ledger_count: int = 0
    event_ledger_chain_ok: bool = False
    strict_world: bool = True
    hidden_transfer: Optional[Dict[str, Any]] = None
    thoughts: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: List[Dict[str, Any]] = field(default_factory=list)
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    theory_ranking: List[Dict[str, Any]] = field(default_factory=list)


class CognitiveOrchestrator:
    """Two-level cognition on CCOS: Thought → Reasoning → Evidence."""

    def __init__(
        self,
        seed: int = 42,
        use_world_loop: bool = True,
        strict_world: bool = True,
        ledger_path: Optional[Path | str] = None,
    ):
        self.seed = seed
        self.use_world_loop = use_world_loop
        self.strict_world = strict_world

        self.heart = CognitiveHeart()
        self.thought = ThoughtEngine(seed=seed)
        self.reasoning = ReasoningEngine()
        self.patterns = PatternDiscoveryEngine()
        self.concepts = ConceptFormationEngine()
        self.serendipity = SerendipityEngine(seed=seed + 3)
        self.theory_comp = TheoryCompetition()
        self.hyp_evo = HypothesisEvolution()

        self.questions = QuestionEngine()
        self.q_eval = QuestionEvaluator()
        self.ideas = IdeaEngine(seed=seed)
        self.creativity = CreativityEngine(seed=seed)
        self.arena = MADArena()
        self.imagination = ImaginationEngine()
        self.causal = CausalEngine()
        self.abstraction = AbstractionEngine()
        self.transfer = TransferEngine()
        self.fp = FingerprintEngine()
        self.invention = InventionEngine()
        self.meta = MetaCognition()
        self.consolidation = ConsolidationEngine()
        self.curriculum = CurriculumEngine()
        self.emergence = EmergenceDetector()
        self.hidden_bench = HiddenDomainBenchmark()

        self.archive: List[str] = []
        self.episodes: List[Dict[str, Any]] = []
        self.theories: List[Theory] = []
        self.ledger: List[Dict[str, Any]] = []
        self.memory_fragments: List[str] = []

        if ledger_path is None:
            ledger_path = Path(tempfile.mkdtemp(prefix="nexus_ledger_")) / "nexus_events.db"
        self.event_bridge = NexusLedgerBridge(ledger_path)
        self.cycle_id = new_id()
        self.event_bridge.set_correlation(self.cycle_id)

        for name, pipe in [
            ("thought_reason_exp", ["thought", "reasoning", "mad", "experiment"]),
            ("analogy_abs_transfer", ["analogy", "abstraction", "transfer"]),
            ("anomaly_causal", ["anomaly", "causal", "intervention"]),
        ]:
            self.meta.register_strategy(
                StrategyGenome(name=name, pipeline=pipe, traits={"seed": 1.0}, fitness=0.4)
            )

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        row = {"type": event_type, **payload}
        self.ledger.append(row)
        try:
            self.event_bridge.emit(event_type, payload)
        except Exception as e:
            self.ledger.append({"type": "ledger_emit_error", "error": str(e)})

    def run_cycle(
        self,
        domain: str = "thermodynamics",
        prediction_errors: Optional[List[Dict[str, Any]]] = None,
        observations: Optional[List[Dict[str, Any]]] = None,
        run_world_experiment: bool = True,
        run_hidden_transfer: bool = True,
    ) -> CycleResult:
        notes: List[str] = []
        prediction_errors = prediction_errors or [
            {
                "entity": "thermal_system",
                "predicted": "stable_delta",
                "actual": "converging",
                "surprise": 0.7,
            }
        ]
        observations = observations or [{"domain": domain, "kind": "state"}]

        self._emit("cycle_start", {"cycle_id": self.cycle_id, "domain": domain, "seed": self.seed})

        objective, salience = self.heart.evaluate_focus(
            observations=observations,
            prediction_errors=prediction_errors,
            archive_size=len(self.archive),
            competence=self.meta.q.capability,
            q=self.meta.q,
            domain=domain,
        )
        self._emit(
            "cognitive_heart",
            {
                "drive": objective.primary_drive.value,
                "priority": objective.priority,
                "top_salience": [
                    {"id": s.item_id, "score": s.score, "desc": s.description}
                    for s in salience[:3]
                ],
            },
        )

        focus_desc = salience[0].description if salience else objective.description

        pattern_hits = self.patterns.scan(self.memory_fragments + self.archive, domain=domain)
        if pattern_hits:
            self._emit("pattern_discovery", {"patterns": pattern_hits[:5]})

        clusters = self.memory_fragments + self.archive + pattern_hits
        if not clusters:
            clusters = ["thermo", "selection", "resource_equalization", "compression"]
        avg_surprise = 0.0
        if prediction_errors:
            avg_surprise = sum(float(e.get("surprise", 0.5)) for e in prediction_errors) / len(
                prediction_errors
            )
        novelty_hunger = max(0.15, 1.0 - min(1.0, len(self.archive) / 8.0))
        plateau = max(0.0, self.meta.q.capability * (1.0 - novelty_hunger) * 0.8)
        serendipity_thoughts = self.serendipity.maybe_link(
            clusters,
            domain=domain,
            novelty_hunger=novelty_hunger,
            plateau=plateau,
            coherence_pressure=0.2,
            resource_pressure=0.2,
            surprise_crisis=avg_surprise if avg_surprise >= 0.85 else avg_surprise * 0.3,
            consolidation_phase=False,
        )
        if serendipity_thoughts:
            self._emit(
                "serendipity",
                {
                    "n": len(serendipity_thoughts),
                    "stats": self.serendipity.stats(),
                    "payload": serendipity_thoughts[0].payload,
                },
            )

        anomalies = [
            f"{e.get('entity')}:{e.get('predicted')}!={e.get('actual')}"
            for e in prediction_errors
        ]
        thoughts: List[Thought] = self.thought.generate(
            focus_description=focus_desc,
            domain=domain,
            observations=observations,
            memory_fragments=self.memory_fragments + self.archive,
            anomalies=anomalies,
            n=6,
        )
        thoughts = serendipity_thoughts + thoughts
        thought_dicts = [t.to_dict() for t in thoughts]
        for t in thoughts:
            self._emit(
                "thought",
                {
                    "id": t.thought_id,
                    "kind": t.kind.value,
                    "content": t.content,
                    "salience": t.salience,
                    "novelty": t.novelty,
                    "source": t.source,
                },
            )

        reasoned = self.reasoning.process(thoughts[:5], domain=domain)
        reasoning_dicts = [
            {
                "method": r.method,
                "conclusion": r.conclusion,
                "confidence": r.confidence,
                "falsifiers": r.falsifiers,
                "predictions": r.predictions,
                "thought_ids": r.thought_ids,
            }
            for r in reasoned
        ]
        for rd in reasoning_dicts:
            self._emit("reasoning", rd)

        raw_q = self.questions.from_objective(
            objective,
            prediction_errors=prediction_errors,
            domain=domain,
        )
        selected = self.q_eval.select_top(raw_q, k=2)
        for q in selected:
            self._emit(
                "question",
                {"id": q.question_id, "text": q.text, "kind": q.kind.value, "score": q.score()},
            )

        hypotheses: List[Hypothesis] = []
        advanced_ids: List[str] = []

        for r in reasoned[:3]:
            seed = self.reasoning.to_hypothesis_seed(r)
            hyp = Hypothesis(
                statement=seed["statement"],
                predictions=seed["predictions"],
                confidence=seed["confidence"],
                falsifiers=seed["falsifiers"],
                status="proposed",
            )
            verdict = self.arena.debate(hyp)
            self._emit(
                "mad_verdict",
                {
                    "hypothesis_id": hyp.hypothesis_id,
                    "aggregate": verdict.aggregate,
                    "advanced": verdict.advanced,
                    "critiques": verdict.critiques,
                    "source": "reasoning",
                },
            )
            if verdict.advanced:
                hyp.status = "tested"
                hypotheses.append(hyp)
                advanced_ids.append(hyp.hypothesis_id)

        for q in selected:
            for idea in self.creativity.explore(q, n=2):
                hyp = self.ideas.idea_to_hypothesis(idea, q)
                verdict = self.arena.debate(hyp)
                self._emit(
                    "mad_verdict",
                    {
                        "hypothesis_id": hyp.hypothesis_id,
                        "aggregate": verdict.aggregate,
                        "advanced": verdict.advanced,
                        "source": "idea",
                    },
                )
                if verdict.advanced:
                    hyp.status = "tested"
                    hypotheses.append(hyp)
                    advanced_ids.append(hyp.hypothesis_id)

        ranking: List[Dict[str, Any]] = []
        if hypotheses:
            self.theory_comp.seed_competitors(
                [h.statement[:120] for h in hypotheses[:3]],
                [h.predictions for h in hypotheses[:3]],
            )
            lik = {
                t.theory_id: max(0.2, h.confidence)
                for t, h in zip(self.theory_comp.theories, hypotheses[:3])
            }
            self.theory_comp.update_from_observation(lik)
            ranking = [
                {"statement": t.statement[:80], "posterior": round(t.posterior, 4)}
                for t in self.theory_comp.ranking()
            ]
            self._emit("theory_competition", {"ranking": ranking})

        imagined = self.imagination.select_informative(
            {"uncertainty": self.meta.q.uncertainty},
            ["observe", "fork_experiment", "intervene_temperature", "baseline_control"],
        )
        if imagined:
            self._emit(
                "mental_simulation",
                {"action": imagined.action, "ig": imagined.expected_information_gain},
            )

        models = self.causal.propose_models("heat_flow", "temperature_equalization")
        intervention = self.causal.distinguishing_intervention(models)
        self._emit("causal_intervention", intervention)

        oracle_accepted: Optional[bool] = None
        discovery: Optional[str] = None
        evidence_id: Optional[str] = None
        if run_world_experiment and self.use_world_loop and domain == "thermodynamics":
            try:
                from world.governance.bridge import StrictCCOSClient
                from world.science.loop import ScientificCivilizationLoop

                client = StrictCCOSClient()
                loop = ScientificCivilizationLoop(
                    seed=self.seed, strict=self.strict_world, ccos=client
                )
                result = loop.run_thermodynamics_experiment(agent_id="nexus-scientist")
                oracle_accepted = any(
                    e.get("type") == "oracle_verdict" and e.get("accepted")
                    for e in result.ledger_events
                )
                discovery = result.discovery
                if result.evidence:
                    evidence_id = result.evidence.evidence_id
                self.meta.predict_success("thermo_experiment", base=0.65)
                self.meta.observe_outcome("thermo_experiment", bool(result.success))
                self.episodes.append(
                    {
                        "domain": domain,
                        "description": discovery or str(result.notes),
                        "outcome": "success" if result.success else "failure",
                    }
                )
                self._emit(
                    "world_experiment",
                    {
                        "success": result.success,
                        "discovery": discovery,
                        "oracle_accepted": oracle_accepted,
                        "strict": self.strict_world,
                    },
                )
                if result.success and discovery:
                    self.archive.append(discovery)
                    self.memory_fragments.append(discovery)
                if hypotheses:
                    outcome = "supported" if result.success else "mixed"
                    evolved = self.hyp_evo.evolve(
                        hypotheses[0],
                        outcome=outcome,
                        boundary_hint="near thermal contact equilibrium",
                    )
                    self._emit(
                        "hypothesis_evolution",
                        {
                            "parent": hypotheses[0].hypothesis_id,
                            "child": evolved.hypothesis_id,
                            "statement": evolved.statement[:100],
                            "status": evolved.status,
                        },
                    )
                    hypotheses[0] = evolved
            except Exception as e:
                notes.append(f"world loop error: {e}")
                self._emit("world_experiment_error", {"error": str(e)})

        theory: Optional[Theory] = None
        transfer_info: Optional[Dict[str, Any]] = None
        concept_dicts: List[Dict[str, Any]] = []
        if discovery or hypotheses:
            mechanism = discovery or (
                hypotheses[0].statement[:120] if hypotheses else "unknown_mechanism"
            )
            theory = self.abstraction.to_theory(
                mechanism=mechanism,
                evidence_ids=[evidence_id] if evidence_id else [],
                domain=domain,
                confidence=0.6 if oracle_accepted else 0.35,
            )
            self.theories.append(theory)
            self._emit(
                "theory",
                {
                    "mechanism": theory.mechanism,
                    "confidence": theory.confidence,
                    "theory_id": theory.theory_id,
                },
            )

            concept = self.concepts.form_from_theory(theory)
            concept_dicts.append(
                {
                    "name": concept.name,
                    "definition": concept.definition,
                    "mechanism": concept.mechanism,
                    "confidence": concept.confidence,
                }
            )
            self._emit("concept_formed", concept_dicts[-1])
            self.memory_fragments.append(concept.name)

            src = self.fp.from_thermo_domain()
            tgt = self.fp.from_selection_domain()
            th = self.transfer.propose(theory, src, tgt)
            transfer_info = {
                "target": th.target_domain,
                "similarity": th.similarity,
                "predicted_success": th.predicted_success,
                "failures": th.predicted_failure_modes,
            }
            self._emit("transfer_hypothesis", transfer_info)

        hidden_info: Optional[Dict[str, Any]] = None
        if run_hidden_transfer and (discovery or theory):
            mech = discovery or (theory.mechanism if theory else "unknown")
            hr: HiddenDomainResult = self.hidden_bench.run(
                mechanism=mech,
                evidence_ids=[evidence_id] if evidence_id else [],
            )
            hidden_info = {
                "hidden_domain": hr.hidden_domain,
                "similarity": hr.similarity,
                "predicted_success": hr.predicted_success,
                "transfer_hit": hr.transfer_hit,
                "prediction": hr.hidden_prediction,
                "actual": hr.hidden_actual,
                "notes": hr.notes,
            }
            self._emit("hidden_domain_transfer", hidden_info)
            notes.append(
                "hidden-domain transfer HIT" if hr.transfer_hit else "hidden-domain transfer MISS"
            )

        artifact_id = None
        if hypotheses:
            idea = self.ideas.generate(selected[0], n=1)[0] if selected else None
            if idea:
                spec = self.invention.specify(idea, hypotheses[0], theory)
                artifact_id = spec.artifact_id
                self._emit("artifact_draft", {"artifact_id": artifact_id, "status": spec.status})

        report = self.consolidation.run(self.episodes)
        if report.contradictions:
            notes.extend(report.contradictions)
            self._emit("consolidation", {"contradictions": report.contradictions})
        if report.patterns:
            self._emit("offline_discovery", {"patterns": report.patterns[:5]})

        strat = self.meta.best_strategy()
        if strat and oracle_accepted:
            strat.fitness = min(1.0, strat.fitness + 0.05)
            self._emit("strategy_update", {"strategy": strat.name, "fitness": strat.fitness})

        gen = 0.0
        if hidden_info:
            gen = float(hidden_info.get("similarity", 0.0))
        elif transfer_info:
            gen = float(transfer_info.get("similarity", 0.0))

        intel = IntelligenceVector(
            performance=self.meta.q.capability,
            learning=self.meta.q.learning_rate,
            generality=gen,
            reasoning=0.5 + 0.1 * len(reasoning_dicts),
            creativity=0.4 + 0.1 * len(thoughts),
            metacognition=self.meta.q.calibration,
            autonomy=objective.priority,
            open_endedness=min(1.0, len(self.archive) / 10.0),
        )
        self._emit("intelligence_vector", intel.as_dict())
        self._emit(
            "cycle_end",
            {
                "discovery": discovery,
                "oracle_accepted": oracle_accepted,
                "n_thoughts": len(thoughts),
                "n_reasoning": len(reasoned),
                "hidden_hit": hidden_info.get("transfer_hit") if hidden_info else None,
            },
        )

        return CycleResult(
            objective=objective,
            questions=selected,
            hypotheses=hypotheses,
            arena_advanced=advanced_ids,
            theory=theory,
            transfer=transfer_info,
            artifact_id=artifact_id,
            oracle_accepted=oracle_accepted,
            discovery=discovery,
            q=self.meta.q.as_dict(),
            intelligence=intel.as_dict(),
            notes=notes,
            ledger_events=list(self.ledger),
            event_ledger_count=self.event_bridge.count(),
            event_ledger_chain_ok=self.event_bridge.verify_chain(),
            strict_world=self.strict_world,
            hidden_transfer=hidden_info,
            thoughts=thought_dicts,
            reasoning=reasoning_dicts,
            concepts=concept_dicts,
            theory_ranking=ranking,
        )
