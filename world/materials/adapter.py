"""Materials adapter — simplified stress/strain and phase properties."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

@dataclass
class Material:
    name: str
    density: float = 1.0
    young_modulus: float = 1e9
    yield_stress: float = 1e6
    temperature: float = 300.0

class MaterialsAdapter:
    def __init__(self):
        self.materials: Dict[str, Material] = {}

    def register(self, mat: Material) -> None:
        self.materials[mat.name] = mat

    def strain(self, name: str, stress: float) -> float:
        m = self.materials[name]
        return stress / max(m.young_modulus, 1e-9)

    def yields(self, name: str, stress: float) -> bool:
        return stress >= self.materials[name].yield_stress
