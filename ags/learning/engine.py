"""Learning engine — update knowledge, self-model, skills from outcomes."""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ags.memory.semantic import SemanticMemory
    from ags.memory.self_model import SelfModel
    from ags.memory.episodic import EpisodicStore
    from ags.skills.skill import SkillRegistry


class LearningEngine:
    def __init__(
        self,
        semantic: "SemanticMemory",
        self_model: "SelfModel",
        episodic: "EpisodicStore",
        skills: "SkillRegistry",
        learning_rate: float = 0.3,
    ):
        self.semantic = semantic
        self.self_model = self_model
        self.episodic = episodic
        self.skills = skills
        self.learning_rate = learning_rate

    def from_experiment(
        self,
        hypothesis: Dict[str, Any],
        success: bool,
        evidence_id: str,
        skill_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        conf = float(hypothesis.get("confidence", 0.5))
        new_conf = conf + self.learning_rate * ((0.9 if success else 0.1) - conf)
        self.semantic.store(
            content=str(hypothesis.get("statement", "")),
            domain=str(hypothesis.get("domain", "general")),
            confidence=max(0.05, min(0.95, new_conf)),
            source="experiment",
            source_type="verified" if success else "observation",
            evidence=[evidence_id],
        )
        self.self_model.update_from_experiment(success)
        self.self_model.update_from_hypothesis(success)
        skill = None
        if skill_name:
            skill = self.skills.acquire_from_experiment(
                name=skill_name,
                description=f"Skill from: {hypothesis.get('statement', '')[:80]}",
                domain=str(hypothesis.get("domain", "general")),
                evidence_id=evidence_id,
                success=success,
            )
        self.episodic.record(
            description=f"Learned from experiment: {hypothesis.get('statement', '')[:100]}",
            outcome="success" if success else "failure",
            valence=0.4 if success else -0.3,
            importance=0.7,
            tags=["learning", "experiment"],
        )
        return {
            "confidence": new_conf,
            "skill": skill.name if skill else None,
            "success": success,
        }

    def from_observation(self, content: str, domain: str, confidence: float) -> str:
        return self.semantic.store(
            content=content,
            domain=domain,
            confidence=confidence,
            source="observation",
            source_type="observation",
        )
