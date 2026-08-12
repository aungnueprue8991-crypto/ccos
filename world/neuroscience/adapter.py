"""Neuroscience adapter — minimal rate model (not a brain simulator)."""
from __future__ import annotations
import numpy as np
from typing import Optional

class SimpleNeuralAdapter:
    def __init__(self, n: int = 16, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.n = n
        self.W = rng.normal(0, 0.1, size=(n, n))
        self.r = np.zeros(n)

    def step(self, input_vec: Optional[np.ndarray] = None, dt: float = 0.1) -> np.ndarray:
        inp = input_vec if input_vec is not None else np.zeros(self.n)
        if len(inp) != self.n:
            inp = np.resize(inp, self.n)
        dr = -self.r + np.tanh(self.W @ self.r + inp)
        self.r = self.r + dt * dr
        return self.r.copy()
