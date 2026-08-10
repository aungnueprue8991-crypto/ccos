"""Authorization service — enforces CCOS-001."""

from __future__ import annotations
from typing import Optional
from uuid import uuid4
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class AuthorizationService:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._tokens: dict[str, dict] = {}

    def authorize(
        self,
        subject: str,
        action: str,
        resource: str,
        intent_id: Optional[str] = None,
    ) -> str:
        token = str(uuid4())
        self._tokens[token] = {
            "subject": subject,
            "action": action,
            "resource": resource,
            "intent_id": intent_id,
            "status": "APPROVED",
        }
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="security.authorization",
                    producer_id="cos.security",
                    payload={
                        "authorization_id": token,
                        "subject": subject,
                        "action": action,
                        "resource": resource,
                    },
                )
            )
        return token

    def check(self, token: str) -> bool:
        return self._tokens.get(token, {}).get("status") == "APPROVED"
