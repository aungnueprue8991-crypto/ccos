"""Scientific adapters — numeric, deterministic, quantized. Not full engines."""

from .physics import apply_impulse, apply_force, PhysicsAdapter
from .thermodynamics import ThermodynamicsAdapter, ThermalBody
from .chemistry import ChemistryAdapter, Reaction
from .biology import BiologyAdapter, Population
from .ecology import EcologyAdapter
from .climate import ClimateAdapter

__all__ = [
    "apply_impulse",
    "apply_force",
    "PhysicsAdapter",
    "ThermodynamicsAdapter",
    "ThermalBody",
    "ChemistryAdapter",
    "Reaction",
    "BiologyAdapter",
    "Population",
    "EcologyAdapter",
    "ClimateAdapter",
]
