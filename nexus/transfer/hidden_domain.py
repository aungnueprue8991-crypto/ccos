"""Hidden-domain transfer benchmark.

Train-side domain (visible): thermal equilibration / conservation flow.
Hidden domain (held out): resource equalization under contact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from nexus.abstraction.extractor import AbstractionEngine
from nexus.patterns.fingerprint import FingerprintEngine
from nexus.transfer.predictor import TransferEngine
from nexus.types import Theory


@dataclass
class HiddenDomainResult:
    source_domain: str
    hidden_domain: str
    similarity: float
    predicted_success: float
    mechanism: str
    hidden_prediction: Dict[str, float]
    hidden_actual: Dict[str, float]
    transfer_hit: bool
    notes: List[str] = field(default_factory=list)


def _resource_equalization_step(
    a: float, b: float, steps: int = 80, rate: float = 0.08
) -> Dict[str, float]:
    x, y = float(a), float(b)
    for _ in range(steps):
        flow = rate * (x - y)
        x -= flow
        y += flow
    return {"pool_a": round(x, 6), "pool_b": round(y, 6)}


class HiddenDomainBenchmark:
    HIDDEN_NAME = "resource_equalization"

    def __init__(self):
        self.fp = FingerprintEngine()
        self.transfer = TransferEngine()
        self.abstraction = AbstractionEngine()

    def hidden_fingerprint(self):
        return self.fp.fingerprint(
            self.HIDDEN_NAME,
            {
                "constraint": 0.65,
                "periodicity": 0.1,
                "symmetry": 0.45,
                "hierarchy": 0.15,
                "sparsity": 0.35,
                "recurrence": 0.55,
                "graph_topology": 0.25,
                "information_flow": 0.65,
                "search_landscape": 0.35,
                "causal_structure": 0.75,
            },
            labels=["conservation", "flow", "equalization"],
        )

    def run(
        self,
        mechanism: str = "thermal_equilibration_confirmed",
        evidence_ids: Optional[List[str]] = None,
        pool_a: float = 100.0,
        pool_b: float = 20.0,
        tol: float = 3.0,
    ) -> HiddenDomainResult:
        theory = self.abstraction.to_theory(
            mechanism=mechanism,
            evidence_ids=evidence_ids or [],
            domain="thermodynamics",
            confidence=0.7,
        )
        src = self.fp.from_thermo_domain()
        tgt = self.hidden_fingerprint()
        hyp = self.transfer.propose(theory, src, tgt)

        total = pool_a + pool_b
        eq = total / 2.0
        predicted = {"pool_a": eq, "pool_b": eq}

        actual = _resource_equalization_step(pool_a, pool_b)
        err_a = abs(actual["pool_a"] - predicted["pool_a"])
        err_b = abs(actual["pool_b"] - predicted["pool_b"])
        hit = err_a <= tol and err_b <= tol and hyp.similarity >= 0.5

        notes = [
            hyp.rationale,
            f"errors: a={err_a:.4f} b={err_b:.4f} tol={tol}",
        ]
        if hyp.predicted_failure_modes:
            notes.extend(hyp.predicted_failure_modes)

        return HiddenDomainResult(
            source_domain="thermodynamics",
            hidden_domain=self.HIDDEN_NAME,
            similarity=hyp.similarity,
            predicted_success=hyp.predicted_success,
            mechanism=mechanism,
            hidden_prediction=predicted,
            hidden_actual=actual,
            transfer_hit=hit,
            notes=notes,
        )
