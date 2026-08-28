"""Extended world modules tests."""

from world.core.world import World
from world.core.entity import Transform, Velocity, Mass, Energy, Label
from world.spatial.index import SpatialIndex
from world.replay.engine import ReplayEngine
from world.provenance.record import ProvenanceStore
from world.materials.adapter import MaterialsAdapter, Material
from world.neuroscience.adapter import SimpleNeuralAdapter
from world.environment.terrain import TerrainGenerator
import numpy as np


def test_spatial_index():
    idx = SpatialIndex()
    idx.update(1, 0, 0)
    idx.update(2, 1, 0)
    idx.update(3, 10, 10)
    near = idx.query_radius(0, 0, 2.0)
    assert 1 in near and 2 in near
    assert 3 not in near


def test_replay_determinism():
    def factory():
        w = World(seed=11)
        w.spawn(Label("a", "o"), Transform(0, 1, 0), Velocity(0.1, 0, 0), Mass(1), Energy(10))
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
