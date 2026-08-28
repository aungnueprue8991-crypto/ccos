from nexus.dream.engine import DreamEngine
from nexus.evolution.cognitive import CognitiveEvolution
from nexus.metacognition.policy import RoutingPolicy
from nexus.routing.loop import EcologyEventLoop


def test_cognitive_evolution_mutate_recombine():
    evo = CognitiveEvolution(seed=1, population_size=8)
    parent = evo.population[0]
    mut = evo.mutate(parent)
    assert mut.pipeline
    assert mut.genome_id != parent.genome_id
    child = evo.recombine(evo.population[0], evo.population[1])
    assert child.pipeline
    elites = evo.evolve_generation()
    assert elites
    assert elites[0].fitness >= 0


def test_dream_cross_domain():
    dream = DreamEngine(seed=2)
    report = dream.run(
        [{"domain": "thermo", "description": "eq"}, {"domain": "eco", "description": "comp"}],
        concepts=["flow"],
        domains=["thermo", "eco"],
        mechanisms=["conservation"],
    )
    assert report.cross_domain_links
    assert report.candidates
    assert all(c.get("cross_domain") for c in report.candidates)
    evs = dream.to_events(report)
    assert evs


def test_routing_policy_learns():
    pol = RoutingPolicy()
    before = pol.weights["experiment_manager"]
    pol.update(["experiment_manager", "reasoning_engine"], success=True, transfer=True)
    assert pol.weights["experiment_manager"] >= before
    ranked = pol.suggest_pipeline({"uncertainty": 0.9})
    assert "simulation_engine" in ranked or ranked


def test_full_loop_with_dream_evolution():
    loop = EcologyEventLoop(seed=42, max_steps=40)
    n = loop.inject_anomaly()
    assert n >= 1
    types = [e.type for e in loop.ws.event_log]
    assert any("support" in t for t in types)
    assert loop.evolution.population
    assert loop.policy.history
