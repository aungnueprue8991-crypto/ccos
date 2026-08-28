"""AGSAgent — developmental organism. LLM is one component; identity persists."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ags.shared.database import configure, get_db
from ags.shared.types import AgentState, Question, new_id
from ags.genome.traits import AgentGenome
from ags.genome.manager import GenomeManager
from ags.models.adapter import BaseModelAdapter, MockAdapter, ModelRouter
from ags.memory.working import WorkingMemory
from ags.memory.episodic import EpisodicStore
from ags.memory.semantic import SemanticMemory
from ags.memory.self_model import SelfModel
from ags.memory.world_model import WorldModel
from ags.memory.consolidation import MemoryConsolidator
from ags.motivation.curiosity import CuriosityEngine
from ags.motivation.goals import GoalManager
from ags.skills.skill import SkillRegistry
from ags.sandbox.runtime import SafeSandbox
from ags.learning.engine import LearningEngine
from ags.discovery.engine import DiscoveryEngine


class AGSAgent:
    def __init__(
        self,
        identity: str,
        workspace: str | Path,
        genome: Optional[AgentGenome] = None,
        model: Optional[BaseModelAdapter] = None,
        ccos_client: Any = None,
        agent_id: Optional[str] = None,
    ):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        db_path = self.workspace / "ags.db"
        configure(db_path)
        self.db = get_db(db_path)

        self.agent_id = agent_id or new_id()
        self.identity = identity
        self.ccos = ccos_client

        self.genomes = GenomeManager(str(db_path))
        if genome is None:
            genome = self.genomes.create_random(self.agent_id)
        else:
            if not genome.genome_id:
                genome.genome_id = new_id()
            self.genomes.save(genome, self.agent_id)
        self.genome = genome

        primary = model or MockAdapter()
        self.model = ModelRouter(primary, fallback=MockAdapter())

        mc = genome.memory_config
        slots = max(3, int(mc.working_memory_slots * genome.cognitive.working_memory_capacity + 3))
        self.working = WorkingMemory(capacity=slots)
        self.episodic = EpisodicStore(self.agent_id, capacity=mc.episodic_capacity, db_path=str(db_path))
        self.semantic = SemanticMemory(self.agent_id, db_path=str(db_path))
        self.self_model = SelfModel(self.agent_id, db_path=str(db_path))
        self.world = WorldModel(self.agent_id, db_path=str(db_path))
        self.consolidator = MemoryConsolidator(
            self.working, self.episodic, self.semantic,
            consolidation_rate=genome.learning.consolidation_rate,
        )
        ct = genome.curiosity
        self.curiosity = CuriosityEngine(
            novelty_weight=ct.novelty_weight,
            uncertainty_weight=ct.uncertainty_weight,
            exploration_budget=ct.exploration_budget,
            information_hunger=ct.information_hunger,
            surprise_sensitivity=ct.surprise_sensitivity,
        )
        self.goals = GoalManager(self.agent_id)
        self.skills = SkillRegistry(self.agent_id, db_path=str(db_path))
        self.sandbox = SafeSandbox(timeout_s=3.0)
        self.discovery = DiscoveryEngine(self.model, self.sandbox, self.skills)
        self.learning = LearningEngine(
            self.semantic, self.self_model, self.episodic, self.skills,
            learning_rate=genome.learning.learning_rate,
        )

        self.state = AgentState(
            agent_id=self.agent_id, identity=identity,
            genome_id=genome.genome_id, status="active",
        )
        self._open_questions: List[Question] = []
        self._hypotheses: List[Dict[str, Any]] = []

    def perceive(self, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.working.update_from_observation({"batch": observations})
        for obs in observations:
            entity = str(obs.get("entity", "unknown"))
            for k, v in obs.items():
                if k in ("entity", "domain", "confidence"):
                    continue
                self.world.assert_fact(entity, k, v, confidence=float(obs.get("confidence", 0.5)))

        pred_errors = self.world.check_predictions(
            {f"{o.get('entity')}.{k}": v for o in observations for k, v in o.items()
             if k not in ("entity", "domain", "confidence")}
        )
        signals = self.curiosity.score_observations(observations)
        signals += self.curiosity.score_prediction_errors(pred_errors)
        domains = list({str(o.get("domain", "general")) for o in observations})
        gaps = self.semantic.get_knowledge_gaps(domains)
        signals += self.curiosity.score_knowledge_gaps(gaps)
        questions = self.curiosity.generate_questions(signals, self.agent_id)
        self._open_questions.extend(questions)
        self.goals.from_questions(questions)
        self.goals.abandon_stale()

        for q in questions:
            self.episodic.record(
                description=f"Question formed: {q.text}",
                importance=q.urgency, tags=["question", q.source], valence=0.1,
            )

        self.state.experience_count += 1
        return {
            "signals": len(signals),
            "questions": [q.text for q in questions],
            "prediction_errors": len(pred_errors),
            "exploration_drive": self.curiosity.get_exploration_drive(),
        }

    def hypothesize(self, focus: Optional[str] = None) -> Dict[str, Any]:
        q = self._open_questions[-1].text if self._open_questions else (focus or "unknown pattern")
        context = "\n".join([
            self.working.get_context_summary(),
            self.semantic.get_context_for_llm(limit=5),
            self.world.get_context_for_llm(),
            self.self_model.get_summary_for_llm(),
        ])
        hyp = self.discovery.form_hypothesis(q, context)
        self._hypotheses.append(hyp)
        self.working.store("current_hypothesis", hyp, importance=0.85)
        self.episodic.record(
            description=f"Hypothesis: {hyp['statement']}",
            importance=0.7, tags=["hypothesis"], valence=0.2,
        )
        return hyp

    def experiment(self, hypothesis: Optional[Dict] = None) -> Dict[str, Any]:
        hyp = hypothesis or (self._hypotheses[-1] if self._hypotheses else None)
        if not hyp:
            hyp = self.hypothesize()
        plan = self.discovery.design_experiment(hyp)
        code = plan.get("code") or "print([(n, n*n) for n in range(1, 6)])"
        sbx = self.discovery.run_sandbox_check(str(code))
        success = bool(sbx.get("success", False))
        if success:
            self.state.successful_experiments += 1
        else:
            self.state.failed_experiments += 1
        learned = self.learning.from_experiment(
            hyp, success=success, evidence_id=str(sbx.get("sandbox_id", "")),
            skill_name="run_python_snippet" if success else None,
        )
        self.state.age_ticks += 1
        return {"plan": plan, "sandbox": sbx, "success": success, "learned": learned}

    def reflect(self) -> Dict[str, Any]:
        promoted = self.consolidator.consolidate(self.agent_id)
        text = self.model.generate(
            "Reflect briefly on recent learning and update self-assessment.",
            system=self.self_model.get_summary_for_llm(),
        )
        self.episodic.record(
            description=f"Reflection: {text[:120]}",
            importance=0.4, tags=["reflection"], valence=0.1,
        )
        return {"promoted": promoted, "reflection": text[:300], "self_model": self.self_model.get_all()}

    def step(self, observations: Optional[List[Dict]] = None) -> Dict[str, Any]:
        obs = observations or [{"entity": "seq", "domain": "mathematics", "value": 16, "confidence": 0.4}]
        perc = self.perceive(obs)
        hyp = self.hypothesize()
        exp = self.experiment(hyp)
        ref = self.reflect()
        return {
            "agent_id": self.agent_id,
            "identity": self.identity,
            "perceive": perc,
            "hypothesis": hyp,
            "experiment": exp,
            "reflect": ref,
            "state": {
                "age_ticks": self.state.age_ticks,
                "experience": self.state.experience_count,
                "knowledge": self.semantic.count(),
                "episodes": self.episodic.count(),
                "successes": self.state.successful_experiments,
                "failures": self.state.failed_experiments,
                "open_questions": len(self._open_questions),
            },
            "genome_desc": self.genome.describe(),
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "identity": self.identity,
            "genome": self.genome.describe(),
            "generation": self.genome.generation,
            "state": self.state.__dict__,
            "memory": {
                "working": len(self.working),
                "episodic": self.episodic.count(),
                "semantic": self.semantic.count(),
                "world_facts": self.world.fact_count(),
            },
            "self_model": self.self_model.get_all(),
            "open_questions": len(self._open_questions),
            "hypotheses": len(self._hypotheses),
            "skills": self.skills.count(),
            "goals_active": len(self.goals.active()),
        }
