"""Scientific adapters smoke tests."""

from world.adapters.chemistry import ChemistryAdapter, Reaction
from world.adapters.biology import BiologyAdapter, Population
from world.adapters.ecology import EcologyAdapter
from world.adapters.climate import ClimateAdapter


def test_chemistry_reaction():
    chem = ChemistryAdapter()
    chem.add_species("H2", 2.0)
    chem.add_species("O2", 1.0)
    chem.add_species("H2O", 0.0)
    chem.add_reaction(Reaction("combust", {"H2": 2, "O2": 1}, {"H2O": 2}, rate=0.05))
    for _ in range(20):
        chem.step(1.0)
    assert chem.species["H2O"] > 0


def test_biology_logistic():
    bio = BiologyAdapter()
    bio.add(Population("algae", 10, growth_rate=0.2, carrying_capacity=100))
    for _ in range(30):
        bio.step(1.0)
    assert 10 < bio.populations["algae"].count <= 100


def test_ecology_network():
    eco = EcologyAdapter()
    eco.add_species("rabbit", 50)
    eco.add_species("fox", 5)
    eco.add_interaction("fox", "rabbit", 0.5)
    for _ in range(10):
        eco.step(0.1)
    assert "rabbit" in eco.biomass


def test_climate_field():
    clim = ClimateAdapter(seed=1)
    t = clim.sample(0, 0)
    assert isinstance(t, float)
