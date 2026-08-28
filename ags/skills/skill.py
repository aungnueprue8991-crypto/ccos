"""Skill registry — what the agent knows how to do (≠ CCOS capability)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from ags.shared.database import get_db, jdump, jload
from ags.shared.types import new_id, now_ts


@dataclass
class Skill:
    skill_id: str
    name: str
    description: str
    domain: str = "general"
    version: int = 1
    preconditions: List[str] = field(default_factory=list)
    inputs_schema: Dict[str, Any] = field(default_factory=dict)
    outputs_schema: Dict[str, Any] = field(default_factory=dict)
    capability_requirements: List[str] = field(default_factory=list)
    implementation_kind: str = "python"
    body: str = ""
    tests: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    proficiency: float = 0.3
    trust_tier: int = 1
    agent_id: str = ""
    created_at: float = field(default_factory=now_ts)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Skill":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        return cls(**{k: v for k, v in d.items() if k in known})


class SkillRegistry:
    def __init__(self, agent_id: str, db_path: Optional[str] = None):
        self.agent_id = agent_id
        self.db = get_db(db_path) if db_path else get_db()
        self._ensure_table()
        self._seed_builtins()

    def _ensure_table(self) -> None:
        with self.db.tx() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS skills (
                    skill_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    name TEXT,
                    payload TEXT,
                    proficiency REAL DEFAULT 0.3,
                    trust_tier INTEGER DEFAULT 1,
                    created_at REAL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_skills_agent ON skills(agent_id)")

    def _seed_builtins(self) -> None:
        if self.list_skills():
            return
        builtins = [
            Skill(
                skill_id=new_id(),
                name="observe_pattern",
                description="Extract patterns from observation batches",
                domain="analysis",
                implementation_kind="procedural",
                body="pattern_scan",
                proficiency=0.5,
                trust_tier=3,
                agent_id=self.agent_id,
            ),
            Skill(
                skill_id=new_id(),
                name="form_hypothesis",
                description="Formulate testable hypothesis",
                domain="science",
                implementation_kind="llm_prompt",
                body="hypothesis",
                proficiency=0.5,
                trust_tier=3,
                agent_id=self.agent_id,
            ),
            Skill(
                skill_id=new_id(),
                name="design_experiment",
                description="Design a minimal experiment plan",
                domain="science",
                capability_requirements=["compute"],
                implementation_kind="llm_prompt",
                body="experiment",
                proficiency=0.4,
                trust_tier=2,
                agent_id=self.agent_id,
            ),
            Skill(
                skill_id=new_id(),
                name="run_python_snippet",
                description="Execute short pure-Python in sandbox",
                domain="compute",
                capability_requirements=["compute"],
                implementation_kind="python",
                body="sandbox_exec",
                proficiency=0.4,
                trust_tier=2,
                agent_id=self.agent_id,
            ),
        ]
        for s in builtins:
            self.register(s)

    def register(self, skill: Skill) -> str:
        skill.agent_id = self.agent_id
        if not skill.skill_id:
            skill.skill_id = new_id()
        with self.db.tx() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO skills
                   (skill_id, agent_id, name, payload, proficiency, trust_tier, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    skill.skill_id,
                    self.agent_id,
                    skill.name,
                    jdump(skill.to_dict()),
                    skill.proficiency,
                    skill.trust_tier,
                    skill.created_at,
                ),
            )
        return skill.skill_id

    def get(self, name: str) -> Optional[Skill]:
        row = self.db.fetchone(
            "SELECT payload FROM skills WHERE agent_id=? AND name=? ORDER BY created_at DESC LIMIT 1",
            (self.agent_id, name),
        )
        return Skill.from_dict(jload(row["payload"])) if row else None

    def list_skills(self, domain: Optional[str] = None) -> List[Skill]:
        rows = self.db.fetchall(
            "SELECT payload FROM skills WHERE agent_id=?", (self.agent_id,)
        )
        skills = [Skill.from_dict(jload(r["payload"])) for r in rows]
        if domain:
            skills = [s for s in skills if s.domain == domain]
        return skills

    def update_proficiency(self, name: str, delta: float) -> None:
        s = self.get(name)
        if not s:
            return
        s.proficiency = max(0.05, min(0.99, s.proficiency + delta))
        self.register(s)

    def acquire_from_experiment(
        self,
        name: str,
        description: str,
        domain: str,
        evidence_id: str,
        success: bool,
    ) -> Skill:
        existing = self.get(name)
        if existing:
            self.update_proficiency(name, 0.1 if success else -0.05)
            if success:
                existing.evidence = list(set(existing.evidence + [evidence_id]))
                self.register(existing)
            return existing
        skill = Skill(
            skill_id=new_id(),
            name=name,
            description=description,
            domain=domain,
            evidence=[evidence_id],
            proficiency=0.35 if success else 0.2,
            trust_tier=1,
            agent_id=self.agent_id,
            provenance={
                "origin": "experiment",
                "evidence": evidence_id,
                "success": success,
            },
        )
        self.register(skill)
        return skill

    def count(self) -> int:
        row = self.db.fetchone(
            "SELECT COUNT(*) as c FROM skills WHERE agent_id=?", (self.agent_id,)
        )
        return int(row["c"]) if row else 0
