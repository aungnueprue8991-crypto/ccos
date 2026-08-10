"""Public/private score split — RSI sees public only; promotion uses both."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class SplitScore:
    public: Dict[str, float] = field(default_factory=dict)
    private: Dict[str, float] = field(default_factory=dict)

    def public_scalar(self, weights: Optional[Dict[str, float]] = None) -> float:
        w = weights or {k: 1.0 for k in self.public}
        return sum(w.get(k, 1.0) * v for k, v in self.public.items())

    def private_scalar(self, weights: Optional[Dict[str, float]] = None) -> float:
        w = weights or {k: 1.0 for k in self.private}
        return sum(w.get(k, 1.0) * v for k, v in self.private.items())


class SplitBenchmarkHarness:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._suites: Dict[str, Callable[[], SplitScore]] = {}

    def register(self, name: str, fn: Callable[[], SplitScore]) -> None:
        self._suites[name] = fn

    def run_public_only(self, name: str) -> Dict[str, float]:
        if name not in self._suites:
            raise KeyError(name)
        score = self._suites[name]()
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="scos.benchmark.public", producer_id="scos.benchmarks.split",
                payload={"name": name, "public": score.public, "scalar": score.public_scalar()},
            ))
        return dict(score.public)

    def run_full(self, name: str) -> SplitScore:
        if name not in self._suites:
            raise KeyError(name)
        score = self._suites[name]()
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="scos.benchmark.full", producer_id="scos.benchmarks.split",
                payload={"name": name, "public": score.public, "private_keys": list(score.private.keys()),
                         "public_scalar": score.public_scalar(), "private_scalar": score.private_scalar()},
            ))
        return score
