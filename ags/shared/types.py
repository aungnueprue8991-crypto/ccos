"""Shared AGS types — identity, memory records, questions."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def new_id() -> str:
    return str(uuid.uuid4())


def now_ts() -> float:
    return time.time()


@dataclass
class EpisodicMemory:
    episode_id: str
    agent_id: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    outcome: str = ""
    emotional_valence: float = 0.0
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass
class KnowledgeItem:
    item_id: str
    agent_id: str
    content: str
    domain: str = "general"
    confidence: float = 0.5
    evidence: List[str] = field(default_factory=list)
    source: str = ""
    source_type: str = "observation"
    verification_status: str = "unverified"
    created_at: float = 0.0
    updated_at: float = 0.0
    access_count: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class Question:
    agent_id: str
    text: str
    domain: str = "general"
    urgency: float = 0.5
    source: str = ""
    question_id: str = field(default_factory=new_id)
    created_at: float = field(default_factory=now_ts)
    status: str = "open"


@dataclass
class AgentState:
    agent_id: str
    identity: str
    genome_id: str = ""
    age_ticks: int = 0
    experience_count: int = 0
    knowledge_count: int = 0
    skill_count: int = 0
    successful_experiments: int = 0
    failed_experiments: int = 0
    discoveries: int = 0
    current_goals: List[str] = field(default_factory=list)
    status: str = "created"
