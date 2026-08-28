"""Phase-1 self-evolution stack: env, profiler, router, efficiency, idle, inspiration."""

from __future__ import annotations

from nexus.efficiency.engine import EfficiencyEngine
from nexus.efficiency.input_filter import InputEfficiencyEngine
from nexus.efficiency.memory_evolution import MemoryEvolutionEngine
from nexus.environment.capabilities import CapabilityDiscovery
from nexus.environment.discovery import EnvironmentDiscovery
from nexus.idle.scheduler import IdleCognitionScheduler
from nexus.inspiration.engine import InspirationEngine
from nexus.memory.hybrid import HybridMemory, MemoryEntry
from nexus.perception.observation import StructuredObservation
from nexus.routing_models.profiler import ModelCapabilityProfiler
from nexus.routing_models.router import CapabilityRouter


def test_environment_discovery():
    env = EnvironmentDiscovery().discover()
    assert env.python_version
    assert env.cpu_count >= 0
    assert env.cwd
    assert isinstance(env.available_commands, list)
    assert env.permissions.get("execute_python") is True


def test_capability_graph_and_gaps():
    env = EnvironmentDiscovery().discover()
    disc = CapabilityDiscovery()
    graph = disc.from_environment(env)
    assert graph.has("python_exec")
    assert graph.has("thought")
    gaps = disc.detect_gaps(graph, ["python_exec", "nonexistent_laser_api"])
    assert "nonexistent_laser_api" in gaps


def test_model_profiler_and_router():
    prof = ModelCapabilityProfiler()
    router = CapabilityRouter(prof)
    d = router.route("math")
    assert d.chosen
    assert d.score > 0
    router.observe(d.chosen, success=True)
    d2 = router.route("coding", prefer_cheap=True)
    assert d2.chosen


def test_input_efficiency_filters():
    eng = InputEfficiencyEngine(threshold=0.3, max_keep=5)
    obs = [
        StructuredObservation(text=f"noise event {i}", prediction_confidence=0.9)
        for i in range(10)
    ]
    obs.append(
        StructuredObservation(
            text="critical anomaly", predicted=0.0, actual=1.0, prediction_confidence=0.1
        )
    )
    batch = eng.filter(obs, state_uncertainty=0.8)
    assert len(batch.kept) <= 5
    assert batch.dropped >= 0


def test_efficiency_and_memory_evolution():
    eff = EfficiencyEngine()
    for i in range(5):
        eff.record(tokens_proxy=2.0 + i, steps=5, success=i % 2 == 0)
    rep = eff.report()
    assert rep.ratio >= 0
    assert rep.recommendations

    mem = HybridMemory()
    mem.write(MemoryEntry(content="thermal equilibration confirmed", domain="thermo", tags=["equilibrium"]))
    mem.write(MemoryEntry(content="resource competition local adaptation", domain="eco", tags=["competition"]))
    ranked = MemoryEvolutionEngine().evaluate(mem)
    assert ranked
    assert ranked[0].name


def test_idle_scheduler():
    sched = IdleCognitionScheduler(budget=1.0)
    tasks = sched.from_signals(
        unresolved_questions=5,
        contradictions=2,
        efficiency_ratio=0.2,
        capability_gaps=["gpu_kernel"],
    )
    assert tasks
    first = sched.next_task()
    assert first is not None
    assert first.priority >= 0


def test_inspiration_cross_domain():
    eng = InspirationEngine()
    cands = eng.inspire("distributed_systems", "load balancing under scarce bandwidth", k=3)
    assert cands
    assert cands[0].source_domain != "distributed_systems" or cands[0].mechanism
    assert cands[0].structural_sim >= 0
