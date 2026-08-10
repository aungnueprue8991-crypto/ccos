"""Citizen runtime — assigns organizational role to an Agent (blueprint §38)."""

from __future__ import annotations
from typing import Optional
from constitution.schemas.citizen import Citizen, CitizenStatus
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class CitizenRuntime:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._citizens: dict[str, Citizen] = {}

    def assign(
        self,
        agent_ref: str,
        organization: str,
        role: str,
        permissions: list[str] | None = None,
        rights: list[str] | None = None,
    ) -> Citizen:
        citizen = Citizen(
            agent_ref=agent_ref,
            organization=organization,
            role=role,
            permissions=permissions or [],
            rights=rights or [],
        )
        self._citizens[citizen.citizen_id] = citizen
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="citizen.assigned",
                    producer_id="governance.citizens",
                    payload={
                        "citizen_id": citizen.citizen_id,
                        "agent_ref": agent_ref,
                        "organization": organization,
                        "role": role,
                    },
                )
            )
        return citizen
