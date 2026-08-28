"""RealityCheck — CCOS epistemic authority.

NEXUS may speculate; only RealityCheck promotes knowledge.
"""

from world.realitycheck.types import (
    Claim,
    ClaimKind,
    ExperimentSpec,
    RealityVerdict,
    VerdictKind,
)
from world.realitycheck.registry import ClaimRegistry
from world.realitycheck.parser import ClaimParser
from world.realitycheck.planner import EvidencePlanner
from world.realitycheck.compiler import ExperimentCompiler
from world.realitycheck.verifiers import (
    CodeVerifier,
    BenchmarkEngine,
    ReproductionEngine,
    AdversarialVerifier,
    SourceValidator,
    DependencyVerifier,
)
from world.realitycheck.verdict import VerdictEngine
from world.realitycheck.authority import RealityAuthority
from world.realitycheck.protocol import ProtocolChecklist, ProtocolRunner, ProtocolVerdict

__all__ = [
    "Claim",
    "ClaimKind",
    "ExperimentSpec",
    "RealityVerdict",
    "VerdictKind",
    "ClaimRegistry",
    "ClaimParser",
    "EvidencePlanner",
    "ExperimentCompiler",
    "CodeVerifier",
    "BenchmarkEngine",
    "ReproductionEngine",
    "AdversarialVerifier",
    "SourceValidator",
    "DependencyVerifier",
    "VerdictEngine",
    "RealityAuthority",
    "ProtocolChecklist",
    "ProtocolRunner",
    "ProtocolVerdict",
]
