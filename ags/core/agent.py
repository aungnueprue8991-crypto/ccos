"""AGSAgent — developmental organism with genome, memory, curiosity, discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ags.shared.database import configure, get_db
from ags.shared.types import AgentState, Question, new_id
from ags.genome.traits import AgentGenome
from ags.genome.manager import GenomeManager
from ags.models.adapter import BaseModelAdapter, MockAdapter
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
from ags.discovery.engine import DiscoveryEngine
from ags.learning.engine import LearningEngine


class AGSAgent:
    """One computational organism; LLM is optional; identity persists."""

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

        self.model = model or MockAdapter()
        self.working = WorkingMemory(capacity=genome.memory_config.working_memory_slots)
        self.episodic = EpisodicStore(
            self.agent_id, capacity=genome.memory_config.episodic_capacity, db_path=str(db_path)
        )
        self.semantic = SemanticMemory(self.agent_id, db_path=str(db_path))
        self.self_model = SelfModel(self.agent_id, db_path=str(db_path))
        self.world = WorldModel(self.agent_id, db_path=str(db_path))
        self.consolidator = MemoryConsolidator(
            self.working,
            self.episodic,
            self.semantic,
            consolidation_rate=genome.learning.consolidation_rate,
        )
        self.curiosity = CuriosityEngine(
            novelty_weight=genome.curiosity.novelty_weight,
            uncertainty_weight=genome.curiosity.uncertainty_weight,
            exploration_budget=genome.curiosity.exploration_budget,
            information_hunger=genome.curiosity.information_hunger,
            surprise_sensitivity=genome.curiosity.surprise_sensitivity,
        )
        self.goals = GoalManager(self.agent_id)
        self.skills = SkillRegistry(self.agent_id, db_path=str(db_path))
        self.sandbox = SafeSandbox()
        self.discovery = DiscoveryEngine(self.model, self.sandbox, self.skills)
        self.learning = LearningEngine(
            self.semantic,
            self.self_model,
            self.episodic,
            self.skills,
            learning_rate=genome.learning.learning_rate,
        )

        self.state = AgentState(
            agent_id=self.agent_id,
            identity=identity,
            genome_id=genome.genome_id,
            status="active",
        )
        self._open_questions: List[Question] = []

    def perceive(self, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.working.update_from_observation({"batch": observations})
        for obs in observations:
            entity = str(obs.get("entity", "unknown"))
            for k, v in obs.items():
                if k in ("entity", "domain", "confidence"):
                    continue
                self.world.assert_fact(
                    entity, k, v, confidence=float(obs.get("confidence", 0.5))
                )

        pred_errors = self.world.check_predictions(
            {
                f"{o.get('entity')}.{k}": v
                for o in observations
                for k, v in o.items()
                if k not in ("entity", "domain", "confidence")
            }
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
                importance=q.urgency,
                tags=["question", q.source],
                valence=0.1,
            )

        self.state.experience_count += 1
        return {
            "signals": len(signals),
            "questions": [q.text for q in questions],
            "goals": [g.description for g in self.goals.top(3)],
            "prediction_errors": len(pred_errors),
        }

    def investigate(self, question: Optional[str] = None) -> Dict[str, Any]:
        """One discovery cycle: hypothesis → experiment design → sandbox check → learn."""
        if question is None:
            if not self._open_questions:
                return {"status": "no_open_questions"}
            q = max(self._open_questions, key=lambda x: x.urgency)
            question = q.text
        ctx = "\n".join([
            self.working.get_context_summary(),
            self.semantic.get_context_for_llm(limit=5),
            self.world.get_context_for_llm(),
        ])
        hyp = self.discovery.form_hypothesis(question, ctx)
        plan = self.discovery.design_experiment(hyp)
        code = plan.get("code") or ""
        run = self.discovery.run_sandbox_check(code)
        learned = self.learning.from_experiment(
            hyp,
            success=bool(run.get("success")),
            evidence_id=str(run.get("sandbox_id", "")),
            skill_name="run_python_snippet" if run.get("success") else None,
        )
        self.consolidate()
        return {
            "question": question,
            "hypothesis": hyp,
            "plan": plan,
            "run": run,
            "learned": learned,
        }

    def consolidate(self) -> int:
        return self.consolidator.consolidate(self.agent_id)

    def status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "identity": self.identity,
            "genome": self.genome.describe(),
            "model": self.model.model_name,
            "experience": self.state.experience_count,
            "knowledge": self.semantic.count(),
            "episodes": self.episodic.count(),
            "skills": self.skills.count(),
            "open_questions": len(self._open_questions),
            "goals": len(self.goals.active()),
            "hypotheses": len(self.discovery.hypotheses),
            "experiments": len(self.discovery.experiments),
        }
