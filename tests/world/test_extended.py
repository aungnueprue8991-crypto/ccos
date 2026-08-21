"""Extended world tests — replay, provenance, materials, neural, terrain."""

import numpy as np

from world.core.world import World
from world.core.entity import Label, Transform, Velocity, Mass, Energy
from world.replay.engine import ReplayEngine
from world.provenance.record import ProvenanceStore
from world.materials.adapter import MaterialsAdapter, Material
from world.neuroscience.adapter import SimpleNeuralAdapter
from world.environment.terrain import TerrainGenerator


def test_replay_roundtrip():
    def factory():
        w = World(seed=3)
        w.spawn(Label("p"), Transform(0, 0, 0), Velocity(0.1, 0, 0), Mass(1), Energy(10))
        return w
    w = factory()
    eng = ReplayEngine()
    rec = eng.record_run(w, ticks=5)
    assert eng.verify(factory, rec)


def test_provenance_store():
    s = ProvenanceStore()
    s.add("experiment", "abc", "def", "0.1.0", 1, agent_id="a1")
    assert s.chain_valid()
    assert len(s.records) == 1


def test_materials():
    m = MaterialsAdapter()
    m.register(Material("steel", young_modulus=200e9, yield_stress=250e6))
    assert m.strain("steel", 200e9) == 1.0
    assert m.elastic_strain("steel", 200e9) == 1.0
    assert m.yields("steel", 300e6)
    total = m.apply_stress("steel", 300e6)
    assert total > m.elastic_strain("steel", 300e6)
    assert m.materials["steel"].plastic_strain > 0


def test_neural_step():
    n = SimpleNeuralAdapter(8, seed=1)
    r = n.step(np.ones(8) * 0.1)
    assert r.shape == (8,)


def test_terrain_seeded():
    t1 = TerrainGenerator(16, 16, seed=5).heightmap()
    t2 = TerrainGenerator(16, 16, seed=5).heightmap()
    assert np.allclose(t1, t2)
    assert not np.allclose(t1, TerrainGenerator(16, 16, seed=6).heightmap())
