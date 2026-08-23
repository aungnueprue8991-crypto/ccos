"""NEXUS — emergent cognitive / scientific layer on CCOS substrate.

CCOS owns kernel, governance, world, evidence, sandbox.
NEXUS owns curiosity→question→hypothesis→experiment design→theory→
abstraction→transfer→invention→meta-learning.

Nothing here mutates live world or registers capabilities without CCOS gates.
"""

from nexus.orchestration.cognitive_loop import CognitiveOrchestrator, CycleResult

__all__ = ["CognitiveOrchestrator", "CycleResult"]
