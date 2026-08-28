"""Self-model — what am I good/bad at?"""

from __future__ import annotations

from typing import Dict, List, Optional

from ags.shared.database import get_db, jdump, jload
from ags.shared.types import new_id, now_ts


class SelfModel:
    def __init__(self, agent_id: str, db_path: Optional[str] = None):
        self.agent_id = agent_id
        self.db = get_db(db_path) if db_path else get_db()
        self._init_defaults()

    def _init_defaults(self) -> None:
        defaults = {
            "reasoning_quality": (0.5, "Estimated quality of reasoning"),
            "hypothesis_accuracy": (0.5, "Accuracy of hypotheses so far"),
            "experiment_success_rate": (0.5, "Rate of successful experiments"),
            "knowledge_breadth": (0.3, "Breadth of knowledge across domains"),
            "knowledge_depth": (0.3, "Depth of knowledge in any domain"),
            "learning_speed": (0.5, "Speed at which skills improve"),
            "curiosity_level": (0.6, "Current curiosity/exploration drive"),
            "goal_completion_rate": (0.5, "Rate of completing set goals"),
        }
        for dim, (val, desc) in defaults.items():
            if not self._get_entry(dim):
                self._upsert(dim, val, desc, [])

    def update(
        self,
        dimension: str,
        value: float,
        evidence_id: Optional[str] = None,
        description: str = "",
    ) -> None:
        existing = self._get_entry(dimension)
        if existing:
            alpha = 0.3
            old = existing["value"]
            new_val = (1 - alpha) * old + alpha * value
            evidence = jload(existing.get("evidence"), [])
            if evidence_id:
                evidence = (evidence + [evidence_id])[-20:]
            self._upsert(
                dimension,
                round(new_val, 4),
                description or existing.get("description") or "",
                evidence,
            )
        else:
            self._upsert(
                dimension,
                value,
                description,
                [evidence_id] if evidence_id else [],
            )

    def get(self, dimension: str) -> Optional[float]:
        row = self._get_entry(dimension)
        return float(row["value"]) if row else None

    def get_all(self) -> Dict[str, float]:
        rows = self.db.fetchall(
            "SELECT dimension, value FROM self_model WHERE agent_id=?", (self.agent_id,)
        )
        return {r["dimension"]: r["value"] for r in rows}

    def get_strengths(self, threshold: float = 0.7) -> List[str]:
        return [k for k, v in self.get_all().items() if v >= threshold]

    def get_weaknesses(self, threshold: float = 0.4) -> List[str]:
        return [k for k, v in self.get_all().items() if v <= threshold]

    def update_from_experiment(self, success: bool) -> None:
        self.update("experiment_success_rate", 1.0 if success else 0.0)

    def update_from_hypothesis(self, confirmed: bool) -> None:
        self.update("hypothesis_accuracy", 1.0 if confirmed else 0.0)

    def get_summary_for_llm(self) -> str:
        all_vals = self.get_all()
        if not all_vals:
            return "Self-model: not yet developed."
        lines = ["Self-model (capabilities and estimates):"]
        for dim, val in sorted(all_vals.items(), key=lambda x: -x[1]):
            bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
            lines.append(f"  {dim:<35} [{bar}] {val:.2f}")
        s, w = self.get_strengths(), self.get_weaknesses()
        if s:
            lines.append(f"  Strengths: {', '.join(s)}")
        if w:
            lines.append(f"  Areas to develop: {', '.join(w)}")
        return "\n".join(lines)

    def _get_entry(self, dimension: str) -> Optional[Dict]:
        return self.db.fetchone(
            "SELECT * FROM self_model WHERE agent_id=? AND dimension=?",
            (self.agent_id, dimension),
        )

    def _upsert(self, dimension: str, value: float, description: str, evidence: List) -> None:
        with self.db.tx() as conn:
            conn.execute(
                """INSERT INTO self_model
                   (entry_id, agent_id, dimension, value, description, evidence, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(agent_id, dimension) DO UPDATE SET
                     value=excluded.value, description=excluded.description,
                     evidence=excluded.evidence, updated_at=excluded.updated_at""",
                (new_id(), self.agent_id, dimension, value, description, jdump(evidence), now_ts()),
            )
