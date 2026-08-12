"""v1.5 Controlled reproduction acceptance tests."""

import random
from ags.evolution.reproduction import (
    ControlledReproduction, StructuredGenome, FitnessVector,
    mutate_genome, crossover,
)


def test_mutation_bounded():
    g = StructuredGenome(genome_id="g0")
    child = mutate_genome(g, rate=1.0, scale=0.05, rng=random.Random(0))
    for v in child.traits.values():
        assert 0.05 <= v <= 0.99


def test_crossover_lineage():
    a = StructuredGenome(genome_id="a", lineage=["a"])
    b = StructuredGenome(genome_id="b", lineage=["b"])
    c = crossover(a, b, random.Random(1))
    assert a.genome_id in c.parents and b.genome_id in c.parents
    assert c.generation == 1


def test_birth_authorized():
    evo = ControlledReproduction(max_population=5)
    g = StructuredGenome(genome_id="p1")
    evo.register("p1", g, FitnessVector(discovery=0.5, learning=0.5))
    tx = evo.request_birth(["p1"], mode="mutate", rng=random.Random(2))
    assert tx.approved
    assert evo.summary()["population"] == 2


def test_population_limit_denies():
    evo = ControlledReproduction(max_population=1)
    evo.register("p1", StructuredGenome("p1"), FitnessVector(discovery=1.0))
    tx = evo.request_birth(["p1"])
    assert not tx.approved
    assert tx.reason == "population_limit"


def test_offspring_quota():
    evo = ControlledReproduction(max_population=10, max_offspring_per_parent=1)
    evo.register("p1", StructuredGenome("p1"), FitnessVector(discovery=1.0))
    assert evo.request_birth(["p1"], rng=random.Random(1)).approved
    tx2 = evo.request_birth(["p1"], rng=random.Random(2))
    assert not tx2.approved and tx2.reason == "offspring_quota"


def test_insufficient_fitness_denies():
    evo = ControlledReproduction()
    evo.register("p1", StructuredGenome("p1"), FitnessVector(discovery=0.0, learning=0.0))
    tx = evo.request_birth(["p1"])
    assert not tx.approved and tx.reason == "insufficient_fitness"


def test_crossover_birth():
    evo = ControlledReproduction(max_population=5)
    evo.register("a", StructuredGenome("a"), FitnessVector(discovery=0.8))
    evo.register("b", StructuredGenome("b"), FitnessVector(discovery=0.8))
    tx = evo.request_birth(["a", "b"], mode="crossover", rng=random.Random(3))
    assert tx.approved
