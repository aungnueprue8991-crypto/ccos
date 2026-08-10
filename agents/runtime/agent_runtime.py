"""Agent runtime — identity, private memory namespace, capabilities, event stream."""

from __future__ import annotations
from typing import Optional
from constitution.schemas.citizen import Agent
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class AgentRuntime:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self._agents: dict[str, Agent] = {}

    def spawn(self, identity: str, memory_namespace: str = "agent") -> Agent:
        agent = Agent(identity=identity, memory_namespace=memory_namespace)
        self._agents[agent.agent_id] = agent
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="agent.spawned",
                    producer_id="agents.runtime",
                    payload={"agent_id": agent.agent_id, "identity": identity},
                )
            )
        return agent

    def get(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)
