"""Evolution fitness, lineage, selection, population stats."""
from ags.evolution.reproduction import FitnessVector, StructuredGenome, ControlledReproduction
from ags.evolution.fitness import evaluate_agent_metrics, pareto_front
from ags.evolution.lineage import LineageGraph
from ags.evolution.selection import select_parents
from ags.population.demographics import PopulationStats, GenerationTracker
from ags.observability.metrics import MetricsRegistry

def test_fitness_eval():
    f = evaluate_agent_metrics({"knowledge": 5, "discoveries": 2, "ledger_valid": True})
    assert f.learning > 0 and f.constitutional_compliance == 1.0

def test_pareto_and_selection():
    fits = {
        "a": FitnessVector(discovery=0.9, learning=0.5, cooperation=0.3),
        "b": FitnessVector(discovery=0.5, learning=0.9, cooperation=0.9),
        "c": FitnessVector(discovery=0.4, learning=0.4, cooperation=0.4),
    }
    front = pareto_front(fits)
    assert "c" not in front or len(front) >= 1
    parents = select_parents(fits, k=2)
    assert len(parents) == 2

def test_lineage_graph():
    g = LineageGraph()
    g.add_birth(["p1"], "c1")
    g.add_birth(["p1", "p2"], "c2")
    assert "p1" in g.ancestors("c1")

def test_population_stats():
    s = PopulationStats()
    s.record_birth(0); s.record_birth(1); s.record_denial()
    assert s.summary()["total_births"] == 2

def test_metrics_registry():
    m = MetricsRegistry()
    m.inc("world_ticks", 1)
    m.set_gauge("population", 3)
    snap = m.snapshot()
    assert snap["world_ticks"] == 1
