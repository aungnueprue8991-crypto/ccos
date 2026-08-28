"""World model — beliefs, predictions, causal hypotheses."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ags.shared.database import get_db, jdump, jload
from ags.shared.types import new_id, now_ts


class WorldModel:
    def __init__(self, agent_id: str, db_path: Optional[str] = None):
        self.agent_id = agent_id
        self.db = get_db(db_path) if db_path else get_db()
        self._pending_predictions: List[Dict] = []

    def assert_fact(
        self,
        entity: str,
        property_name: str,
        value: Any,
        confidence: float = 0.5,
        evidence: Optional[List[str]] = None,
    ) -> str:
        existing = self._get_fact(entity, property_name)
        fact_id = existing["fact_id"] if existing else new_id()
        if existing:
            old_conf = existing["confidence"]
            new_conf = old_conf + 0.3 * (confidence - old_conf)
            new_evidence = list(set(jload(existing.get("evidence"), []) + (evidence or [])))
        else:
            new_conf = confidence
            new_evidence = evidence or []
        with self.db.tx() as conn:
            conn.execute(
                """INSERT INTO world_model
                   (fact_id, agent_id, entity, property, value, confidence, evidence, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(agent_id, entity, property) DO UPDATE SET
                     value=excluded.value, confidence=excluded.confidence,
                     evidence=excluded.evidence, updated_at=excluded.updated_at""",
                (
                    fact_id,
                    self.agent_id,
                    entity,
                    property_name,
                    str(value),
                    new_conf,
                    jdump(new_evidence),
                    now_ts(),
                    now_ts(),
                ),
            )
        return fact_id

    def get_entity(self, entity: str) -> Dict[str, Any]:
        rows = self.db.fetchall(
            "SELECT property, value, confidence FROM world_model WHERE agent_id=? AND entity=? ORDER BY confidence DESC",
            (self.agent_id, entity),
        )
        return {r["property"]: {"value": r["value"], "confidence": r["confidence"]} for r in rows}

    def get_fact(self, entity: str, prop: str) -> Optional[Tuple[str, float]]:
        row = self._get_fact(entity, prop)
        return (row["value"], row["confidence"]) if row else None

    def get_all_entities(self) -> List[str]:
        rows = self.db.fetchall(
            "SELECT DISTINCT entity FROM world_model WHERE agent_id=?", (self.agent_id,)
        )
        return [r["entity"] for r in rows]

    def get_uncertain_facts(self, threshold: float = 0.6) -> List[Dict]:
        rows = self.db.fetchall(
            "SELECT entity, property, value, confidence FROM world_model "
            "WHERE agent_id=? AND confidence<? ORDER BY confidence ASC LIMIT 20",
            (self.agent_id, threshold),
        )
        return [dict(r) for r in rows]

    def make_prediction(
        self,
        entity: str,
        prop: str,
        predicted_value: Any,
        confidence: float = 0.5,
    ) -> str:
        pred_id = new_id()
        self._pending_predictions.append({
            "pred_id": pred_id,
            "entity": entity,
            "property": prop,
            "predicted": str(predicted_value),
            "confidence": confidence,
            "timestamp": now_ts(),
        })
        return pred_id

    def check_predictions(self, observations: Dict[str, Any]) -> List[Dict]:
        errors, resolved = [], []
        for pred in self._pending_predictions:
            obs_key = f"{pred['entity']}.{pred['property']}"
            if obs_key not in observations:
                continue
            actual = str(observations[obs_key])
            if actual != pred["predicted"]:
                surprise = 1.0
                if self._is_numeric(actual) and self._is_numeric(pred["predicted"]):
                    surprise = abs(float(actual) - float(pred["predicted"]))
                errors.append({
                    "pred_id": pred["pred_id"],
                    "entity": pred["entity"],
                    "property": pred["property"],
                    "predicted": pred["predicted"],
                    "actual": actual,
                    "surprise": surprise,
                    "confidence_was": pred["confidence"],
                })
                self.assert_fact(
                    pred["entity"],
                    pred["property"],
                    actual,
                    confidence=min(0.9, pred["confidence"] * 0.7),
                )
            resolved.append(pred["pred_id"])
        self._pending_predictions = [
            p for p in self._pending_predictions if p["pred_id"] not in resolved
        ]
        return errors

    def assert_causal(
        self,
        cause: str,
        effect: str,
        confidence: float = 0.4,
        evidence: Optional[List[str]] = None,
    ) -> None:
        self.assert_fact(f"causal:{cause}", "causes", effect, confidence, evidence)

    def get_causes_of(self, effect: str) -> List[Tuple[str, float]]:
        rows = self.db.fetchall(
            "SELECT entity, confidence FROM world_model WHERE agent_id=? AND property='causes' AND value=? ORDER BY confidence DESC",
            (self.agent_id, effect),
        )
        return [(r["entity"].replace("causal:", ""), r["confidence"]) for r in rows]

    def get_context_for_llm(self, entities: Optional[List[str]] = None) -> str:
        all_entities = entities or self.get_all_entities()[:6]
        if not all_entities:
            return "World model: no beliefs formed yet."
        lines = ["World model (beliefs about environment):"]
        for entity in all_entities:
            props = self.get_entity(entity)
            if props:
                lines.append(f"  {entity}:")
                for prop, info in list(props.items())[:4]:
                    lines.append(
                        f"    .{prop} = {info['value']} (confidence: {info['confidence']:.0%})"
                    )
        return "\n".join(lines)

    def fact_count(self) -> int:
        row = self.db.fetchone(
            "SELECT COUNT(*) as c FROM world_model WHERE agent_id=?", (self.agent_id,)
        )
        return int(row["c"]) if row else 0

    def _get_fact(self, entity: str, prop: str) -> Optional[Dict]:
        return self.db.fetchone(
            "SELECT * FROM world_model WHERE agent_id=? AND entity=? AND property=?",
            (self.agent_id, entity, prop),
        )

    @staticmethod
    def _is_numeric(s: str) -> bool:
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False
