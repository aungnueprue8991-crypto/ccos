"""Multi-agent population manager — spawn, role assignment, basic coordination."""

from __future__ import annotations

from typing import Dict, List, Optional

from constitution.schemas.citizen import Agent, Citizen
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger
from agents.runtime.agent_runtime import AgentRuntime
from governance.citizens.runtime import CitizenRuntime


class PopulationManager:
    def __init__(
        self,
        agent_runtime: AgentRuntime,
        citizen_runtime: CitizenRuntime,
        ledger: Optional[EventLedger] = None,
    ):
        self.agents = agent_runtime
        self.citizens = citizen_runtime
        self.ledger = ledger
        self._population: Dict[str, dict] = {}

    def spawn_citizen(
        self,
        identity: str,
        organization: str,
        role: str,
        permissions: list[str] | None = None,
        capabilities: list[str] | None = None,
    ) -> tuple[Agent, Citizen]:
        agent = self.agents.spawn(identity=identity, memory_namespace=f"agent:{identity}")
        if capabilities:
            agent.capabilities = capabilities
        citizen = self.citizens.assign(
            agent_ref=agent.agent_id,
            organization=organization,
            role=role,
            permissions=permissions or [],
            rights=["observe", "propose"] if role != "governor" else ["observe", "propose", "decide"],
        )
        self._population[agent.agent_id] = {
            "identity": identity,
            "role": role,
            "organization": organization,
            "citizen_id": citizen.citizen_id,
        }
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="agents.population.spawned",
                    producer_id="agents.population",
                    payload={
                        "agent_id": agent.agent_id,
                        "citizen_id": citizen.citizen_id,
                        "role": role,
                        "organization": organization,
                    },
                )
            )
        return agent, citizen

    def list_population(self) -> List[dict]:
        return list(self._population.values())

    def by_role(self, role: str) -> List[dict]:
        return [p for p in self._population.values() if p["role"] == role]

    def size(self) -> int:
        return len(self._population)
