"""Climate adapter — seasonal, diurnal, and latitudinal temperature + precipitation fields."""

from __future__ import annotations

import math
from typing import Dict

import numpy as np


def _q(x: float, nd: int = 3) -> float:
    return round(float(x), nd)


class ClimateAdapter:
    def __init__(self, width: int = 16, height: int = 16, seed: int = 0):
        self.width = width
        self.height = height
        self.time = 0.0
        rng = np.random.default_rng(seed)
        lat = np.linspace(-1.0, 1.0, height).reshape(-1, 1)
        self.base = 25.0 - 18.0 * np.abs(lat) + rng.normal(0, 1.5, size=(height, width))
        self.moisture = np.clip(
            0.4 + 0.2 * (1.0 - np.abs(lat)) + rng.normal(0, 0.05, size=(height, width)),
            0.05, 1.0,
        )

    def step(self, dt: float = 1.0) -> np.ndarray:
        self.time += dt
        seasonal = 6.0 * math.sin(self.time * 0.1)
        diurnal = 2.0 * math.sin(self.time * 0.8)
        field = self.base + seasonal + diurnal
        return np.round(field, 3)

    def precipitation(self) -> np.ndarray:
        seasonal = 0.5 + 0.5 * math.sin(self.time * 0.1 + 0.5)
        return np.round(self.moisture * 10.0 * seasonal, 3)

    def sample(self, x: int, y: int) -> float:
        field = self.step(0)
        x = int(np.clip(x, 0, self.width - 1))
        y = int(np.clip(y, 0, self.height - 1))
        return float(field[y, x])

    def sample_precip(self, x: int, y: int) -> float:
        p = self.precipitation()
        x = int(np.clip(x, 0, self.width - 1))
        y = int(np.clip(y, 0, self.height - 1))
        return float(p[y, x])

    def regional_mean(self) -> Dict[str, float]:
        field = self.step(0)
        precip = self.precipitation()
        return {
            "temp_mean": _q(float(np.mean(field))),
            "temp_min": _q(float(np.min(field))),
            "temp_max": _q(float(np.max(field))),
            "precip_mean": _q(float(np.mean(precip))),
            "time": _q(self.time, 2),
        }

    def anomaly(self, x: int, y: int) -> float:
        field = self.step(0)
        x = int(np.clip(x, 0, self.width - 1))
        y = int(np.clip(y, 0, self.height - 1))
        return _q(float(field[y, x] - np.mean(field)))
