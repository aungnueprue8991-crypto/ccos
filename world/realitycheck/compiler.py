"""Claim → Experiment Compiler."""

from __future__ import annotations

from typing import Dict

from world.realitycheck.parser import ClaimParser
from world.realitycheck.planner import EvidencePlanner
from world.realitycheck.registry import ClaimRegistry
from world.realitycheck.types import Claim, ExperimentSpec


class ExperimentCompiler:
    def __init__(self, registry: ClaimRegistry | None = None):
        self.registry = registry or ClaimRegistry()
        self.parser = ClaimParser()
        self.planner = EvidencePlanner()

    def compile(
        self,
        statement: str,
        domain: str = "general",
        metrics: Dict[str, float] | None = None,
        baseline: Dict[str, float] | None = None,
        model_confidence: float = 0.0,
    ) -> tuple[Claim, ExperimentSpec]:
        claim = self.parser.parse(
            statement,
            domain=domain,
            model_confidence=model_confidence,
            metrics=metrics,
            baseline=baseline,
        )
        self.registry.register(claim)
        spec = self.planner.plan(claim)
        return claim, spec

    def compile_claim(self, claim: Claim) -> ExperimentSpec:
        self.registry.register(claim)
        return self.planner.plan(claim)
