"""Neuroscience adapter — deterministic rate network with Hebbian plasticity.

Not a brain simulator: small N, quantized state, optional energy budget.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np


def _q_arr(a: np.ndarray, nd: int = 6) -> np.ndarray:
    return np.round(a, nd)


class SimpleNeuralAdapter:
    def __init__(self, n: int = 16, seed: int = 0, tau: float = 1.0):
        rng = np.random.default_rng(seed)
        self.n = n
        self.tau = max(1e-3, tau)
        self.W = rng.normal(0, 0.1, size=(n, n))
        np.fill_diagonal(self.W, 0.0)
        self.r = np.zeros(n)
        self.energy = 1.0
        self.t = 0.0
        self.learning_rate = 0.0

    def step(self, input_vec: Optional[np.ndarray] = None, dt: float = 0.1) -> np.ndarray:
        inp = input_vec if input_vec is not None else np.zeros(self.n)
        if len(inp) != self.n:
            inp = np.resize(inp, self.n)
        scale = max(0.1, min(1.0, self.energy))
        drive = self.W @ self.r + inp * scale
        dr = (-self.r + np.tanh(drive)) / self.tau
        self.r = _q_arr(self.r + dt * dr)
        self.t += dt
        self.energy = float(max(0.0, self.energy - 0.001 * dt * float(np.mean(np.abs(self.r)))))
        if self.learning_rate > 0:
            self._hebbian(dt)
        return self.r.copy()

    def _hebbian(self, dt: float) -> None:
        outer = np.outer(self.r, self.r)
        self.W = self.W + self.learning_rate * dt * (outer - 0.01 * self.W)
        np.fill_diagonal(self.W, 0.0)
        self.W = _q_arr(self.W, 5)

    def inject(self, indices: Tuple[int, ...], value: float = 1.0) -> np.ndarray:
        inp = np.zeros(self.n)
        for i in indices:
            if 0 <= i < self.n:
                inp[i] = value
        return self.step(inp)

    def mean_rate(self) -> float:
        return float(np.round(np.mean(self.r), 6))

    def snapshot(self) -> Dict[str, float]:
        return {
            "n": float(self.n),
            "t": float(np.round(self.t, 4)),
            "mean_rate": self.mean_rate(),
            "energy": float(np.round(self.energy, 6)),
            "w_norm": float(np.round(np.linalg.norm(self.W), 6)),
        }
