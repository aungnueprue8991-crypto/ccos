"""Materials adapter — elastic/plastic response, thermal expansion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


def _q(x: float, nd: int = 8) -> float:
    return round(float(x), nd)


@dataclass
class Material:
    name: str
    density: float = 1.0
    young_modulus: float = 1e9
    yield_stress: float = 1e6
    temperature: float = 300.0
    thermal_expansion: float = 1e-5
    melt_k: float = 1800.0
    plastic_strain: float = 0.0


class MaterialsAdapter:
    def __init__(self):
        self.materials: Dict[str, Material] = {}

    def register(self, mat: Material) -> None:
        self.materials[mat.name] = mat

    def elastic_strain(self, name: str, stress: float) -> float:
        m = self.materials[name]
        return _q(stress / max(m.young_modulus, 1e-9))

    def strain(self, name: str, stress: float) -> float:
        m = self.materials[name]
        return _q(self.elastic_strain(name, stress) + m.plastic_strain)

    def apply_stress(self, name: str, stress: float) -> float:
        m = self.materials[name]
        if abs(stress) >= m.yield_stress:
            over = abs(stress) - m.yield_stress
            m.plastic_strain = _q(m.plastic_strain + over / max(m.young_modulus, 1e-9))
        return self.strain(name, stress)

    def yields(self, name: str, stress: float) -> bool:
        return abs(stress) >= self.materials[name].yield_stress

    def set_temperature(self, name: str, temp_k: float) -> float:
        m = self.materials[name]
        m.temperature = max(0.0, float(temp_k))
        return m.temperature

    def thermal_strain(self, name: str, temp_k: float, t_ref: float = 300.0) -> float:
        m = self.materials[name]
        return _q(m.thermal_expansion * (temp_k - t_ref))

    def phase(self, name: str) -> str:
        m = self.materials[name]
        return "liquid" if m.temperature >= m.melt_k else "solid"

    def effective_modulus(self, name: str) -> float:
        m = self.materials[name]
        if m.temperature >= m.melt_k:
            return _q(m.young_modulus * 0.01)
        frac = m.temperature / max(m.melt_k, 1.0)
        return _q(m.young_modulus * max(0.05, 1.0 - 0.5 * frac))

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        out = {}
        for n, m in sorted(self.materials.items()):
            out[n] = {
                "density": m.density,
                "E": m.young_modulus,
                "E_eff": self.effective_modulus(n),
                "yield": m.yield_stress,
                "T": m.temperature,
                "plastic_strain": m.plastic_strain,
                "phase": 1.0 if self.phase(n) == "liquid" else 0.0,
            }
        return out
