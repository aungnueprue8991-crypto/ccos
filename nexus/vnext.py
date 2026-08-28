"""NEXUS vNext facade — hierarchical system connecting all layers.

Does not replace engines; orchestrates:
  Reality → CCOS/World → Perception → Heart → Thought → Reasoning
  → Autonomous Discovery Loop → Evidence → Meta → New state
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from nexus.world_model.core import WorldModel
from nexus.perception.binding import BindingEngine, RawModality
from nexus.perception.observation import ObservationEngine
from nexus.perception.salience import SalienceEngine
from nexus.efficiency.input_filter import InputEfficiencyEngine
from nexus.routing_models.router import CapabilityRouter
from nexus.routing.loop import EcologyEventLoop
from nexus.epistemic.evidence_gate import EvidenceGate, BeliefStatus
from nexus.epistemic.contradiction import ContradictionEngine
from nexus.epistemic.curiosity import CuriosityAllocator
from nexus.discovery.experiment_select import ExperimentSelector
from nexus.discovery.research import AutonomousResearchEngine
from nexus.discovery.self_optimize import SelfOptimizationLoop
from nexus.idle.scheduler import IdleCognitionScheduler
from nexus.efficiency.engine import EfficiencyEngine
from nexus.memory.hybrid import HybridMemory
from nexus.memory.compression import MemoryCompressionEngine
from nexus.inspiration.engine import InspirationEngine
from world.realitycheck.authority import RealityAuthority


@dataclass
class VNextResult:
    phase: str
    discovery: Optional[str] = None
    belief_status: Optional[str] = None
    events: int = 0
    world: Dict[str, Any] = field(default_factory=dict)
    research_queue: List[str] = field(default_factory=list)
    efficiency: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


class NexusVNext:
    """Single entry for hierarchical cognitive/discovery system."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.world = WorldModel()
        self.binding = BindingEngine()
        self.observation = ObservationEngine()
        self.salience = SalienceEngine()
        self.input_filter = InputEfficiencyEngine(threshold=0.3)
        self.router = CapabilityRouter()
        self.ecology = EcologyEventLoop(seed=seed, max_steps=35)
        self.gate = EvidenceGate()
        self.contradictions = ContradictionEngine()
        self.curiosity = CuriosityAllocator()
        self.experiments = ExperimentSelector()
        self.research = AutonomousResearchEngine()
        self.optimize = SelfOptimizationLoop()
        self.idle = IdleCognitionScheduler()
        self.efficiency = EfficiencyEngine()
        self.memory = HybridMemory()
        self.compression = MemoryCompressionEngine()
        self.inspiration = InspirationEngine()
        self.reality = RealityAuthority()

    def boot(self) -> Dict[str, Any]:
        snap = self.world.refresh(needed_caps=["python_exec", "thought"])
        self.world.update_self(status="booted", seed=self.seed)
        route = self.router.route("reasoning")
        return {
            "status": "READY",
            "world": snap.to_dict(),
            "route_reasoning": route.chosen,
            "capabilities": snap.capabilities[:15],
        }

    def run_discovery_from_observation(
        self,
        text: str = "thermal system prediction mismatch",
        predicted: float = 0.0,
        actual: float = 1.0,
    ) -> VNextResult:
        notes = []
        percept = self.binding.bind([
            RawModality("text", text),
            RawModality("environment", {"entity": "thermal_system"}),
        ])
        obs = self.observation.normalize(
            percept, domain="thermodynamics",
            predicted=predicted, actual=actual, prediction_confidence=0.3,
        )
        batch = self.input_filter.filter([obs], state_uncertainty=0.7)
        notes.append(f"kept={len(batch.kept)} dropped={batch.dropped}")

        route = self.router.route("reasoning")
        notes.append(f"routed_to={route.chosen}")

        ticks = self.ecology.inject_anomaly(
            predicted=predicted, actual=actual, confidence=0.3, text=text
        )
        types = [e.type for e in self.ecology.ws.event_log]
        support = any("support" in t for t in types)
        discovery = None
        for e in self.ecology.ws.event_log:
            if e.payload.get("discovery"):
                discovery = e.payload["discovery"]

        claim = self.gate.register(
            discovery or "thermal equilibration",
            source="ecology",
            predictions=["temperature_equalization"],
        )
        claim = self.gate.assess(
            claim.claim_id,
            oracle_accepted=support,
            prediction_match=0.9 if support else 0.3,
        )

        rc_verdict = None
        if discovery:
            rc_verdict = self.reality.check_memory_compression_claim(
                compression_ratio=0.72, accuracy_loss=0.013
            )
            notes.append(f"realitycheck={rc_verdict.kind.value}")

        hyps = [h.get("statement", "") for h in self.ecology.ws.hypotheses[-5:]]
        self.contradictions.detect(hyps)

        self.efficiency.record(tokens_proxy=float(ticks), steps=ticks, success=support)

        qs = [q.get("text", "") for q in self.ecology.ws.questions[-5:] if q.get("text")]
        self.research.enqueue_from_gaps(qs, contradictions=self.contradictions.open_count())

        self.idle.from_signals(
            unresolved_questions=len(qs),
            contradictions=self.contradictions.open_count(),
            efficiency_ratio=self.efficiency.report().ratio,
        )

        return VNextResult(
            phase="discovery",
            discovery=discovery,
            belief_status=claim.status.value,
            events=len(types),
            world=self.world.refresh().to_dict(),
            research_queue=[r.question for r in self.research.queue[:5]],
            efficiency=self.efficiency.report().as_dict(),
            notes=notes,
        )

    def run_idle_cycle(self) -> Dict[str, Any]:
        task = self.idle.next_task()
        if not task:
            self.idle.from_signals(unresolved_questions=1)
            task = self.idle.next_task()
        out: Dict[str, Any] = {"task": task.name if task else None, "kind": task.kind if task else None}
        if task and task.kind in ("cross_domain", "serendipity", "research"):
            ideas = self.research.explore_cross_domain("computing", "scarce resource allocation")
            out["ideas"] = ideas
        if task and task.kind == "efficiency":
            out["efficiency"] = self.efficiency.report().as_dict()
        if task and task.kind == "consolidation":
            if not self.memory.entries:
                from nexus.memory.hybrid import MemoryEntry
                self.memory.write(MemoryEntry(content="thermal equilibration", tags=["eq"], domain="thermo"))
            out["compression"] = self.compression.compress_and_validate(self.memory).__dict__
        return out
