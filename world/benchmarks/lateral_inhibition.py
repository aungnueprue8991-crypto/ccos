"""Lateral inhibition — competitive dynamics (WTA-style) as a pure simulation.

Biological idea: active units suppress neighbors → contrast / winner-take-all.
Computational form: recurrent inhibition until one (or k) units dominate.

Mapping to systems (hypothesis, not fact):
  event handlers / DB connections compete under a budget the way
  neural populations compete under inhibition — strongest demand wins,
  others are suppressed (queued or dropped), sharpening allocation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class InhibitionStep:
    activations: List[float]
    winner_index: int


def competitive_select(
    inputs: Sequence[float],
    *,
    inhibition: float = 0.35,
    self_excitation: float = 0.15,
    steps: int = 12,
    soft: bool = False,
) -> InhibitionStep:
    a = [float(x) for x in inputs]
    n = len(a)
    if n == 0:
        return InhibitionStep(activations=[], winner_index=-1)
    for _ in range(steps):
        total = sum(a)
        nxt = []
        for i in range(n):
            others = total - a[i]
            v = a[i] + self_excitation * a[i] - inhibition * others
            nxt.append(max(0.0, v))
        s = sum(nxt) or 1.0
        if soft:
            a = [x / s for x in nxt]
        else:
            a = nxt
    if not soft and sum(a) > 0:
        w = max(range(n), key=lambda i: a[i])
        a = [1.0 if i == w else 0.0 for i in range(n)]
    winner = max(range(n), key=lambda i: a[i]) if a else -1
    return InhibitionStep(activations=a, winner_index=winner)


class LateralInhibitionSim:
    def run(self, inputs: Sequence[float], **kwargs) -> InhibitionStep:
        return competitive_select(inputs, **kwargs)

    def resource_allocation_analogy(
        self,
        demands: Sequence[float],
        capacity: float = 1.0,
    ) -> dict:
        step = competitive_select(demands, soft=True, steps=15)
        alloc = [x * capacity for x in step.activations]
        return {
            "demands": list(demands),
            "activations": step.activations,
            "allocations": alloc,
            "winner": step.winner_index,
            "analogy": "lateral_inhibition->competitive_resource_grant",
        }
