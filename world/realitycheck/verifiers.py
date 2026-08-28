"""Verifiers — code, benchmark, reproduction, adversarial, source, dependency."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from world.realitycheck.types import ExperimentSpec


@dataclass
class VerifyResult:
    name: str
    passed: bool
    measurements: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


class CodeVerifier:
    def verify(
        self,
        spec: ExperimentSpec,
        run_fn: Optional[Callable[[], Dict[str, float]]] = None,
    ) -> VerifyResult:
        if run_fn is None:
            return VerifyResult("code", False, notes=["no_run_fn"])
        try:
            measurements = dict(run_fn())
        except Exception as e:
            return VerifyResult("code", False, notes=[f"error:{e}"])
        met = {}
        for k, thresh in spec.success_criteria.items():
            val = measurements.get(k.replace("_min", "").replace("_max", ""), measurements.get(k))
            if val is None:
                if "compression" in k:
                    val = measurements.get("compression_ratio")
                elif "accuracy" in k:
                    val = measurements.get("accuracy_loss", measurements.get("retrieval_fidelity"))
            if val is None:
                met[k] = False
                continue
            if k.endswith("_min") or "min" in k:
                met[k] = float(val) >= float(thresh)
            elif k.endswith("_max") or "max" in k or "loss" in k:
                met[k] = float(val) <= float(thresh)
            else:
                met[k] = float(val) >= float(thresh)
        passed = all(met.values()) if met else False
        return VerifyResult("code", passed, measurements=measurements, notes=[f"criteria={met}"])


class BenchmarkEngine:
    def run(self, measurements: Dict[str, float], baseline: Dict[str, float]) -> VerifyResult:
        gains = {}
        for k, b in baseline.items():
            if k in measurements and b:
                gains[f"gain_{k}"] = (measurements[k] - b) / abs(b) if b else 0.0
        return VerifyResult("benchmark", True, measurements=gains, notes=["benchmark_recorded"])


class ReproductionEngine:
    def reproduce(
        self,
        run_fn: Callable[[], Dict[str, float]],
        n: int = 2,
        tol: float = 0.15,
    ) -> VerifyResult:
        rng_results = []
        try:
            for _ in range(n):
                rng_results.append(run_fn())
        except Exception as e:
            return VerifyResult("reproduction", False, notes=[f"error:{e}"])
        if len(rng_results) < 2:
            return VerifyResult("reproduction", False, notes=["insufficient_trials"])
        keys = set(rng_results[0])
        for r in rng_results[1:]:
            keys &= set(r)
        stable = True
        agg = {}
        for k in keys:
            vals = [float(r[k]) for r in rng_results]
            mu = sum(vals) / len(vals)
            agg[k] = mu
            if mu == 0:
                continue
            spread = max(vals) - min(vals)
            if abs(spread / (abs(mu) + 1e-9)) > tol:
                stable = False
        return VerifyResult("reproduction", stable, measurements=agg, notes=[f"trials={n}"])


class AdversarialVerifier:
    def probe(
        self,
        measurements: Dict[str, float],
        tests: List[str],
        seed: int = 0,
    ) -> VerifyResult:
        rng = random.Random(seed)
        stressed = {}
        notes = []
        for t in tests:
            noise = 1.0 - 0.05 * rng.random()
            for k, v in measurements.items():
                stressed[f"{k}_adv_{t}"] = float(v) * noise
            notes.append(t)
        passed = all(float(v) == float(v) for v in stressed.values())
        if measurements.get("compression_ratio", 1) < 0.1 and "compression_ratio" in measurements:
            passed = False
            notes.append("adversarial_collapse")
        return VerifyResult("adversarial", passed, measurements=stressed, notes=notes)


class SourceValidator:
    def validate(self, statement: str, known_sources: Optional[List[str]] = None) -> VerifyResult:
        known_sources = known_sources or []
        score = 0.0
        notes = []
        for s in known_sources:
            if any(w in statement.lower() for w in s.lower().split()[:3]):
                score = max(score, 0.6)
                notes.append(f"overlap:{s[:40]}")
        return VerifyResult(
            "source", score >= 0.5, measurements={"source_support": score}, notes=notes or ["no_source"]
        )


class DependencyVerifier:
    def check(self, required: List[str], available: List[str]) -> VerifyResult:
        missing = [r for r in required if r not in available]
        return VerifyResult(
            "dependency",
            len(missing) == 0,
            measurements={"missing": float(len(missing))},
            notes=missing or ["deps_ok"],
        )
