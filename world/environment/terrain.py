"""Deterministic terrain generation from seed."""
from __future__ import annotations
import numpy as np

class TerrainGenerator:
    def __init__(self, width: int = 64, height: int = 64, seed: int = 0):
        self.width, self.height, self.seed = width, height, seed

    def heightmap(self) -> np.ndarray:
        rng = np.random.default_rng(self.seed)
        h = np.zeros((self.height, self.width))
        for scale, amp in [(4, 1.0), (8, 0.5), (16, 0.25)]:
            noise = rng.normal(0, 1, size=(scale, scale))
            up = np.kron(noise, np.ones((self.height // scale or 1, self.width // scale or 1)))
            up = up[:self.height, :self.width]
            h += amp * up
        return np.round(h, 4)

    def biome_mask(self, heightmap: np.ndarray) -> np.ndarray:
        out = np.zeros_like(heightmap, dtype=int)
        out[heightmap > 0.5] = 1
        out[heightmap > 1.5] = 2
        out[heightmap > 2.5] = 3
        return out
