"""Climate adapter — seasonal temperature field."""
from __future__ import annotations
import math
import numpy as np

class ClimateAdapter:
    def __init__(self, width: int = 8, height: int = 8, seed: int = 0):
        self.width, self.height, self.time = width, height, 0
        rng = np.random.default_rng(seed)
        self.base = 15.0 + rng.normal(0, 2, size=(height, width))

    def step(self, dt: float = 1.0) -> np.ndarray:
        self.time += dt
        seasonal = 5.0 * math.sin(self.time * 0.1)
        return np.round(self.base + seasonal, 3)

    def sample(self, x: int, y: int) -> float:
        field = self.step(0)
        x = int(np.clip(x, 0, self.width - 1))
        y = int(np.clip(y, 0, self.height - 1))
        return float(field[y, x])
