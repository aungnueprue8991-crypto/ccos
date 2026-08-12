"""Population statistics and generation tracking."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from collections import defaultdict

@dataclass
class GenerationTracker:
    current: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def advance(self, metrics: Dict[str, Any]) -> None:
        self.history.append({"generation": self.current, **metrics})
        self.current += 1

class PopulationStats:
    def __init__(self):
        self.by_generation: Dict[int, int] = defaultdict(int)
        self.total_births = 0
        self.total_denials = 0

    def record_birth(self, generation: int) -> None:
        self.by_generation[generation] += 1
        self.total_births += 1

    def record_denial(self) -> None:
        self.total_denials += 1

    def summary(self) -> Dict[str, Any]:
        return {
            "total_births": self.total_births,
            "total_denials": self.total_denials,
            "by_generation": dict(self.by_generation),
        }
