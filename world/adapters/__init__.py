"""Scientific adapters — numeric, deterministic, quantized."""

from .thermodynamics import ThermodynamicsAdapter, ThermalBody
from .chemistry import ChemistryAdapter, Reaction
from .biology import BiologyAdapter, Population
from .ecology import EcologyAdapter
from .climate import ClimateAdapter
from .physics import apply_impulse, apply_force, PhysicsAdapter

__all__ = [
    "ThermodynamicsAdapter",
    "ThermalBody",
    "ChemistryAdapter",
    "Reaction",
    "BiologyAdapter",
    "Population",
    "EcologyAdapter",
    "ClimateAdapter",
    "apply_impulse",
    "apply_force",
    "PhysicsAdapter",
]
