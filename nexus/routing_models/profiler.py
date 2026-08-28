"""Model Capability Profiler — static + light probe profiles for available models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class ModelProfile:
    model_id: str
    reasoning: float = 0.5
    coding: float = 0.5
    mathematics: float = 0.5
    vision: float = 0.0
    audio: float = 0.0
    tool_use: float = 0.5
    long_context: float = 0.5
    latency: float = 0.5
    cost: float = 0.5
    hallucination_risk: float = 0.4
    context_size: int = 8192
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    meta: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def score_for(self, task_type: str) -> float:
        mapping = {
            "reasoning": self.reasoning,
            "coding": self.coding,
            "math": self.mathematics,
            "mathematics": self.mathematics,
            "vision": self.vision,
            "audio": self.audio,
            "tool": self.tool_use,
            "tool_use": self.tool_use,
            "long_context": self.long_context,
            "fast": self.latency,
            "cheap": 1.0 - self.cost,
        }
        base = mapping.get(task_type, 0.5)
        if task_type in ("math", "coding", "reasoning"):
            base *= 1.0 - 0.3 * self.hallucination_risk
        return max(0.0, min(1.0, base))


class ModelCapabilityProfiler:
    """Registry of profiles; includes symbolic/local engines as first-class models."""

    def __init__(self):
        self.profiles: Dict[str, ModelProfile] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        self.profiles["local_symbolic"] = ModelProfile(
            model_id="local_symbolic",
            reasoning=0.7, coding=0.4, mathematics=0.85, tool_use=0.6,
            latency=0.95, cost=0.05, hallucination_risk=0.1, context_size=10_000,
            strengths=["math", "deterministic"], weaknesses=["open_language"],
        )
        self.profiles["nexus_engines"] = ModelProfile(
            model_id="nexus_engines",
            reasoning=0.75, coding=0.5, mathematics=0.6, tool_use=0.8,
            latency=0.9, cost=0.1, hallucination_risk=0.15,
            strengths=["theory_competition", "experiment"], weaknesses=["open_chat"],
        )
        self.profiles["generic_llm"] = ModelProfile(
            model_id="generic_llm",
            reasoning=0.7, coding=0.7, mathematics=0.55, vision=0.4,
            tool_use=0.65, long_context=0.7, latency=0.4, cost=0.6,
            hallucination_risk=0.45, context_size=128_000,
            strengths=["language", "planning"], weaknesses=["guaranteed_truth"],
        )

    def register(self, profile: ModelProfile) -> None:
        self.profiles[profile.model_id] = profile

    def get(self, model_id: str) -> Optional[ModelProfile]:
        return self.profiles.get(model_id)

    def all_profiles(self) -> List[ModelProfile]:
        return list(self.profiles.values())
