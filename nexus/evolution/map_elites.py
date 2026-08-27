"""MAP-Elites 2.0 lite — archive of cognitive strategies over behavior space.

Axes (discrete): analytical↔exploratory, causal↔analogical
Each cell holds best-performing routing/strategy genome.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

from ags.shared.types import new_id


@dataclass
class StrategyCell:
    cell_id: str  # e.g. "analytical_causal"
    analytical: float  # 0=exploratory .. 1=analytical
    causal: float  # 0=analogical .. 1=causal
    name: str = ""
    pipeline: List[str] = field(default_factory=list)
    fitness: float = 0.0
    trials: int = 0
    genome_id: str = field(default_factory=new_id)

    def as_dict(self) -> dict:
        return asdict(self)


def _bin(v: float, n: int = 3) -> int:
    v = max(0.0, min(0.999, v))
    return int(v * n)


class CognitiveMapElites:
    def __init__(self, bins: int = 3):
        self.bins = bins
        self.archive: Dict[Tuple[int, int], StrategyCell] = {}
        seeds = [
            ("analytical_causal", 0.9, 0.9, ["reason", "causal", "experiment"]),
            ("analytical_analogical", 0.9, 0.1, ["analogy", "transfer", "reason"]),
            ("exploratory_causal", 0.1, 0.9, ["thought", "serendipity", "experiment"]),
            ("exploratory_analogical", 0.1, 0.1, ["serendipity", "analogy", "dream"]),
            ("balanced", 0.5, 0.5, ["thought", "reason", "mad", "experiment"]),
        ]
        for name, a, c, pipe in seeds:
            self.try_add(name, a, c, pipe, fitness=0.4)

    def _key(self, analytical: float, causal: float) -> Tuple[int, int]:
        return (_bin(analytical, self.bins), _bin(causal, self.bins))

    def try_add(
        self,
        name: str,
        analytical: float,
        causal: float,
        pipeline: List[str],
        fitness: float,
    ) -> bool:
        key = self._key(analytical, causal)
        cell = self.archive.get(key)
        if cell is None or fitness > cell.fitness:
            self.archive[key] = StrategyCell(
                cell_id=f"{key[0]}_{key[1]}",
                analytical=analytical,
                causal=causal,
                name=name,
                pipeline=list(pipeline),
                fitness=fitness,
                trials=(cell.trials + 1) if cell else 1,
            )
            return True
        cell.trials += 1
        return False

    def best(self) -> Optional[StrategyCell]:
        if not self.archive:
            return None
        return max(self.archive.values(), key=lambda c: c.fitness)

    def select_for_state(self, uncertainty: float, novelty_pressure: float) -> StrategyCell:
        """High uncertainty → more exploratory; high novelty pressure → analogical."""
        analytical = 1.0 - 0.6 * uncertainty
        causal = 1.0 - 0.5 * novelty_pressure
        key = self._key(analytical, causal)
        if key in self.archive:
            return self.archive[key]
        return self.best() or StrategyCell(
            cell_id="default", analytical=0.5, causal=0.5, name="default",
            pipeline=["thought", "reason", "experiment"], fitness=0.3,
        )

    def observe_outcome(self, cell: StrategyCell, success: bool, transfer: bool = False) -> None:
        delta = 0.05 if success else -0.03
        if transfer:
            delta += 0.04
        new_fit = max(0.0, min(1.0, cell.fitness + delta))
        self.try_add(cell.name, cell.analytical, cell.causal, cell.pipeline, new_fit)

    def coverage(self) -> float:
        return len(self.archive) / (self.bins * self.bins)
