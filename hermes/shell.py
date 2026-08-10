"""Hermes — production CCOS application / orchestrator shell (frontier wiring)."""

from __future__ import annotations

from pathlib import Path

from constitution.schemas.intent import Intent, IntentStatus
from constitution.schemas.event import EventEnvelope
from constitution.config import get_config
from constitution.invariants import InvariantMonitor
from kernel.events.ledger import EventLedger
from kernel.events.bus import EventBus
from kernel.events.replication import ReplicationCluster
from kernel.registry.capability_registry import CapabilityRegistry
from kernel.security.authorization import AuthorizationService
from kernel.scheduler.scheduler import Scheduler
from kernel.resources.manager import ResourceManager, Quota
from kernel.ipc.channels import IPC
from kernel.lifecycle.manager import LifecycleManager
from kernel.diagnostics.health import Diagnostics
from cognition.evidence.pipeline import EvidencePipeline
from cognition.memory.governance import MemoryGovernance
from cognition.planning.planner import Planner
from cognition.beliefs.store import BeliefStore
from cognition.knowledge.graph import KnowledgeGraph
from cognition.world_model.model import WorldModel
from cognition.experience.recorder import ExperienceRecorder
from cognition.reasoning.backend import DeterministicReasoner
from governance.decisions.engine import GovernanceEngine
from governance.citizens.runtime import CitizenRuntime
from governance.organizations.registry import OrganizationRegistry
from governance.policies.evaluator import PolicyEvaluator
from evolution.promotion.pipeline import PromotionPipeline
from evolution.hypotheses.engine import HypothesisEngine
from evolution.experiments.runner import ExperimentRunner
from evolution.benchmarks.harness import BenchmarkHarness
from evolution.rollback.manager import RollbackManager
from agents.runtime.agent_runtime import AgentRuntime
from agents.population.manager import PopulationManager
from agents.civilization.runtime import CivilizationRuntime
from simulation.cosmos import ArtificialCosmos
from simulation.physics import PhysicsCosmos
from observatory.core import Observatory
from rich.console import Console

console = Console()


class Hermes:
    """Full constitutional stack orchestrator — every plane wired."""

    def __init__(self, workspace: str | Path = "."):
        self.cfg = get_config(workspace)
        self.workspace = self.cfg.workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.cfg.storage_dir.mkdir(exist_ok=True)
        (self.workspace / "observatory" / "ledger").mkdir(parents=True, exist_ok=True)

        self.ledger = EventLedger(self.cfg.ledger_path)
        self.bus = EventBus(self.ledger)
        self.observatory = Observatory(self.ledger)
        self.registry = CapabilityRegistry(self.ledger, self.cfg.storage_dir / "capabilities.db")
        self.auth = AuthorizationService(self.ledger)
        self.scheduler = Scheduler(self.ledger)
        self.resources = ResourceManager(self.ledger)
        self.ipc = IPC(self.ledger)
        self.lifecycle = LifecycleManager(self.ledger)
        self.diagnostics = Diagnostics(self.ledger)
        self.invariants = InvariantMonitor(self.ledger)
        self.replication = ReplicationCluster()

        self.evidence = EvidencePipeline(self.ledger, self.cfg.storage_dir / "evidence.db")
        self.memory = MemoryGovernance(self.ledger, self.cfg.storage_dir / "memory.db")
        self.planner = Planner(self.ledger)
        self.beliefs = BeliefStore(self.ledger, self.cfg.storage_dir / "beliefs.db")
        self.knowledge = KnowledgeGraph(self.ledger, self.cfg.storage_dir / "knowledge.db")
        self.world_model = WorldModel(self.ledger, self.cfg.storage_dir / "world_model.db")
        self.experience = ExperienceRecorder(self.ledger, self.cfg.storage_dir / "experience.db")
        self.reasoner = DeterministicReasoner(self.ledger)

        self.governance = GovernanceEngine(self.ledger)
        self.citizens = CitizenRuntime(self.ledger)
        self.organizations = OrganizationRegistry(self.ledger, self.cfg.storage_dir / "organizations.db")
        self.policies = PolicyEvaluator(self.ledger)

        self.promotion = PromotionPipeline(self.ledger, self.registry, self.governance)
        self.hypotheses = HypothesisEngine(self.ledger, self.cfg.storage_dir / "hypotheses.db")
        self.experiments = ExperimentRunner(self.ledger)
        self.benchmarks = BenchmarkHarness(self.ledger)
        self.rollback = RollbackManager(self.registry, self.ledger)

        self.agent_runtime = AgentRuntime(self.ledger)
        self.population = PopulationManager(self.agent_runtime, self.citizens, self.ledger)
        self.civilization = CivilizationRuntime(self.population, self.organizations, self.ledger)
        self.cosmos = ArtificialCosmos(self.ledger)
        self.physics = PhysicsCosmos(self.ledger)

        if getattr(self.cfg, "enable_scheduler", False):
            self.scheduler.start()

        self.bus.publish(
            EventEnvelope(
                event_type="cos.boot",
                producer_id="cos.kernel",
                payload={
                    "status": "kernel_ready",
                    "workspace": str(self.workspace.resolve()),
                    "constitution_version": getattr(self.cfg, "constitution_version", "1.0.0"),
                    "planes": ["cos", "cog", "scos", "governance", "agents", "simulation", "observatory", "replication"],
                },
            )
        )
        console.print("[bold magenta]Hermes ready[/bold magenta] — full production substrate online")

    def submit_intent(self, issuer: str, objective: str, constraints: list[str] | None = None) -> Intent:
        intent = Intent(
            issuer=issuer, objective=objective, constraints=constraints or [],
            status=IntentStatus.COMMITTED, immutable_root=True,
        )
        intent.root_intent = intent.intent_id
        self.bus.publish(
            EventEnvelope(
                event_type="hermes.intent", producer_id="hermes",
                payload={"intent_id": intent.intent_id, "issuer": issuer, "objective": objective},
            )
        )
        return intent

    def health(self):
        return self.diagnostics.check(ledger=self.ledger, memory_ok=True)

    def status(self) -> dict:
        return self.observatory.reconstruction_summary()
