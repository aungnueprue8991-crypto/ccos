"""Thermodynamics adapter — Q = m c ΔT and simple heat transfer (canonical)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ThermalBody:
    name: str
    mass_kg: float
    temp_k: float
    c_j_per_kg_k: float = 4180.0


class ThermodynamicsAdapter:
    VERSION = "0.1.0"

    def __init__(self):
        self.bodies: Dict[str, ThermalBody] = {}

    def add_body(self, body: ThermalBody) -> None:
        self.bodies[body.name] = body

    def apply_heat(self, name: str, q_joules: float) -> float:
        b = self.bodies[name]
        dt = q_joules / max(b.mass_kg * b.c_j_per_kg_k, 1e-12)
        b.temp_k = round(b.temp_k + dt, 6)
        return b.temp_k

    def heat_transfer(
        self, a: str, b: str, k: float = 1.0, area: float = 1.0, dist: float = 1.0, dt: float = 1.0
    ) -> None:
        ba, bb = self.bodies[a], self.bodies[b]
        dq = k * area * (ba.temp_k - bb.temp_k) / max(dist, 1e-9) * dt
        self.apply_heat(a, -dq)
        self.apply_heat(b, dq)

    def step_pair(
        self, a: str, b: str, steps: int = 10, dt: float = 0.1, k: float = 50.0
    ) -> Dict[str, float]:
        for _ in range(steps):
            self.heat_transfer(a, b, k=k, dt=dt)
        return {n: self.bodies[n].temp_k for n in (a, b)}

    def snapshot(self) -> Dict[str, float]:
        return {n: round(b.temp_k, 6) for n, b in sorted(self.bodies.items())}
