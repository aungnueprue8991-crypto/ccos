"""Planning remains pure — emits PlanningEvent; does not know about UERs (blueprint §11)."""

from __future__ import annotations
from typing import Any, Optional
from uuid import uuid4
from constitution.schemas.event import EventEnvelope
from constitution.schemas.intent import Intent
from kernel.events.ledger import EventLedger


class Planner:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger

    def plan(self, intent: Intent, assumptions: list[str] | None = None) -> dict[str, Any]:
        plan = {
            "plan_id": str(uuid4()),
            "intent_id": intent.intent_id,
            "objective": intent.objective,
            "assumptions": assumptions or [],
            "candidate_actions": [],
            "expected_outcomes": [],
            "constraints": intent.constraints,
            "confidence": 0.5,
        }
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="cog.planning",
                    producer_id="cog.planner",
                    payload=plan,
                    correlation_id=intent.intent_id,
                )
            )
        return plan
