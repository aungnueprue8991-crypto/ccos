"""AGS Genome Traits — structured, versioned developmental parameters."""

from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class CognitiveTraits:
    reasoning_depth: float = 0.6
    abstraction_bias: float = 0.5
    analogy_tendency: float = 0.5
    systematic_bias: float = 0.6
    attention_breadth: float = 0.5
    working_memory_capacity: float = 0.6


@dataclass
class CuriosityTraits:
    novelty_weight: float = 0.7
    uncertainty_weight: float = 0.65
    exploration_budget: float = 0.6
    information_hunger: float = 0.7
    surprise_sensitivity: float = 0.6
    depth_vs_breadth: float = 0.5


@dataclass
class LearningTraits:
    consolidation_rate: float = 0.5
    forgetting_rate: float = 0.02
    experimentation_bias: float = 0.6
    learning_rate: float = 0.3
    error_sensitivity: float = 0.7
    transfer_tendency: float = 0.5


@dataclass
class ExplorationTraits:
    epsilon: float = 0.3
    optimism_bias: float = 0.4
    risk_tolerance: float = 0.5
    novelty_bonus: float = 0.6
    persistence: float = 0.6


@dataclass
class SocialTraits:
    cooperation_bias: float = 0.6
    teaching_bias: float = 0.5
    trust_threshold: float = 0.5
    communication_frequency: float = 0.4
    social_learning_weight: float = 0.5


@dataclass
class PlanningTraits:
    planning_horizon: int = 5
    lookahead_depth: int = 3
    goal_commitment: float = 0.6
    replanning_threshold: float = 0.4
    subgoal_granularity: float = 0.5


@dataclass
class PersonalityTraits:
    patience: float = 0.5
    confidence_calibration: float = 0.6
    reflection_tendency: float = 0.5
    caution: float = 0.4
    openness: float = 0.7


@dataclass
class MemoryConfiguration:
    episodic_capacity: int = 1000
    semantic_decay_threshold: float = 0.1
    working_memory_slots: int = 7
    consolidation_interval: int = 10
    importance_threshold: float = 0.3


@dataclass
class AgentGenome:
    genome_id: str = ""
    version: int = 1
    generation: int = 0
    cognitive: CognitiveTraits = field(default_factory=CognitiveTraits)
    curiosity: CuriosityTraits = field(default_factory=CuriosityTraits)
    learning: LearningTraits = field(default_factory=LearningTraits)
    exploration: ExplorationTraits = field(default_factory=ExplorationTraits)
    social: SocialTraits = field(default_factory=SocialTraits)
    planning: PlanningTraits = field(default_factory=PlanningTraits)
    personality: PersonalityTraits = field(default_factory=PersonalityTraits)
    memory_config: MemoryConfiguration = field(default_factory=MemoryConfiguration)
    skill_affinities: Dict[str, float] = field(default_factory=dict)
    preferred_model: str = "mock/test"
    fallback_model: str = "mock/test"
    parent_genome_ids: List[str] = field(default_factory=list)
    mutation_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "version": self.version,
            "generation": self.generation,
            "cognitive": asdict(self.cognitive),
            "curiosity": asdict(self.curiosity),
            "learning": asdict(self.learning),
            "exploration": asdict(self.exploration),
            "social": asdict(self.social),
            "planning": asdict(self.planning),
            "personality": asdict(self.personality),
            "memory_config": asdict(self.memory_config),
            "skill_affinities": self.skill_affinities,
            "preferred_model": self.preferred_model,
            "fallback_model": self.fallback_model,
            "parent_genome_ids": self.parent_genome_ids,
            "mutation_history": self.mutation_history,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentGenome":
        g = cls(
            genome_id=d.get("genome_id", ""),
            version=d.get("version", 1),
            generation=d.get("generation", 0),
            preferred_model=d.get("preferred_model", "mock/test"),
            fallback_model=d.get("fallback_model", "mock/test"),
            skill_affinities=d.get("skill_affinities") or {},
            parent_genome_ids=list(d.get("parent_genome_ids") or []),
            mutation_history=list(d.get("mutation_history") or []),
        )
        for name, typ in [
            ("cognitive", CognitiveTraits),
            ("curiosity", CuriosityTraits),
            ("learning", LearningTraits),
            ("exploration", ExplorationTraits),
            ("social", SocialTraits),
            ("planning", PlanningTraits),
            ("personality", PersonalityTraits),
            ("memory_config", MemoryConfiguration),
        ]:
            if name in d and isinstance(d[name], dict):
                setattr(
                    g,
                    name,
                    typ(**{k: v for k, v in d[name].items() if k in typ.__dataclass_fields__}),
                )
        return g

    @classmethod
    def random(cls, genome_id: str = "") -> "AgentGenome":
        def rv(lo=0.1, hi=0.9):
            return round(random.uniform(lo, hi), 3)

        return cls(
            genome_id=genome_id or "",
            cognitive=CognitiveTraits(
                reasoning_depth=rv(),
                abstraction_bias=rv(),
                analogy_tendency=rv(),
                systematic_bias=rv(),
                attention_breadth=rv(),
                working_memory_capacity=rv(0.4, 0.9),
            ),
            curiosity=CuriosityTraits(
                novelty_weight=rv(0.4, 0.95),
                uncertainty_weight=rv(0.3, 0.9),
                exploration_budget=rv(0.3, 0.8),
                information_hunger=rv(0.4, 0.95),
                surprise_sensitivity=rv(0.3, 0.9),
                depth_vs_breadth=rv(),
            ),
            learning=LearningTraits(
                consolidation_rate=rv(0.2, 0.8),
                forgetting_rate=rv(0.01, 0.05),
                experimentation_bias=rv(0.3, 0.8),
                learning_rate=rv(0.1, 0.6),
                error_sensitivity=rv(0.4, 0.9),
                transfer_tendency=rv(),
            ),
            exploration=ExplorationTraits(
                epsilon=rv(0.1, 0.5),
                optimism_bias=rv(0.2, 0.7),
                risk_tolerance=rv(),
                novelty_bonus=rv(0.3, 0.8),
                persistence=rv(0.3, 0.8),
            ),
            social=SocialTraits(
                cooperation_bias=rv(0.3, 0.9),
                teaching_bias=rv(),
                trust_threshold=rv(0.3, 0.8),
                communication_frequency=rv(0.2, 0.7),
                social_learning_weight=rv(),
            ),
            personality=PersonalityTraits(
                patience=rv(),
                confidence_calibration=rv(0.4, 0.8),
                reflection_tendency=rv(0.2, 0.7),
                caution=rv(0.1, 0.7),
                openness=rv(0.4, 0.95),
            ),
        )

    def describe(self) -> str:
        c, p, e, s = self.curiosity, self.personality, self.exploration, self.social
        parts = []
        if c.novelty_weight > 0.7:
            parts.append("highly novelty-seeking")
        elif c.novelty_weight < 0.4:
            parts.append("prefers familiar territory")
        if p.patience > 0.7:
            parts.append("patient")
        elif p.patience < 0.35:
            parts.append("impatient")
        if e.risk_tolerance > 0.7:
            parts.append("risk-tolerant")
        elif e.risk_tolerance < 0.3:
            parts.append("cautious")
        if p.openness > 0.7:
            parts.append("open to new ideas")
        if e.persistence > 0.7:
            parts.append("persistent")
        if s.cooperation_bias > 0.7:
            parts.append("cooperative")
        return "Agent is " + ", ".join(parts) if parts else "Agent has balanced traits"
