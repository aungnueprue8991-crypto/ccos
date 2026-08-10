"""Civilization Runtime — large-scale multi-agent coordination.

Hub-and-spoke + role teams, task market, event-driven coordination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import uuid4

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger
from agents.population.manager import PopulationManager
from governance.organizations.registry import OrganizationRegistry


@dataclass
class Task:
    task_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    role_required: str = "researcher"
    status: str = "open"
    assignee: Optional[str] = None
    result: Optional[dict] = None
    organization: str = ""


class CivilizationRuntime:
    def __init__(
        self,
        population: PopulationManager,
        organizations: OrganizationRegistry,
        ledger: Optional[EventLedger] = None,
    ):
        self.population = population
        self.organizations = organizations
        self.ledger = ledger
        self.tasks: Dict[str, Task] = {}
        self._teams: Dict[str, List[str]] = {}

    def bootstrap_civilization(self, name: str = "CCOS-Civ") -> dict:
        science = self.organizations.create(f"{name}-Science", objectives=["discover", "verify"])
        gov = self.organizations.create(f"{name}-Governance", objectives=["authorize", "audit"])
        infra = self.organizations.create(f"{name}-Infrastructure", objectives=["execute", "observe"])
        roles = [
            ("scientist-1", science.name, "researcher"),
            ("scientist-2", science.name, "researcher"),
            ("verifier-1", science.name, "verifier"),
            ("governor-1", gov.name, "governor"),
            ("operator-1", infra.name, "operator"),
        ]
        for identity, org, role in roles:
            agent, citizen = self.population.spawn_citizen(
                identity, org, role,
                permissions=["experiment"] if role == "researcher" else ["decide"] if role == "governor" else ["execute"],
            )
            self._teams.setdefault(role, []).append(identity)
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="civilization.bootstrapped", producer_id="agents.civilization",
                payload={
                    "name": name,
                    "orgs": [science.name, gov.name, infra.name],
                    "population": self.population.size(),
                    "teams": {k: len(v) for k, v in self._teams.items()},
                },
            ))
        return {
            "name": name,
            "population": self.population.size(),
            "organizations": [science.name, gov.name, infra.name],
            "teams": dict(self._teams),
        }

    def submit_task(self, title: str, role_required: str = "researcher", organization: str = "") -> Task:
        task = Task(title=title, role_required=role_required, organization=organization)
        self.tasks[task.task_id] = task
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="civilization.task.submitted", producer_id="agents.civilization",
                payload={"task_id": task.task_id, "title": title, "role": role_required},
            ))
        return task

    def assign_tasks(self) -> List[Task]:
        assigned = []
        for task in self.tasks.values():
            if task.status != "open":
                continue
            candidates = self._teams.get(task.role_required, [])
            if not candidates:
                continue
            task.assignee = candidates[0]
            task.status = "assigned"
            assigned.append(task)
            if self.ledger:
                self.ledger.append(EventEnvelope(
                    event_type="civilization.task.assigned", producer_id="agents.civilization",
                    payload={"task_id": task.task_id, "assignee": task.assignee},
                ))
        return assigned

    def complete_task(self, task_id: str, result: dict, success: bool = True) -> Task:
        task = self.tasks[task_id]
        task.status = "completed" if success else "failed"
        task.result = result
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="civilization.task.completed", producer_id="agents.civilization",
                payload={"task_id": task_id, "success": success, "result": result},
            ))
        return task

    def status(self) -> dict:
        by_status: Dict[str, int] = {}
        for t in self.tasks.values():
            by_status[t.status] = by_status.get(t.status, 0) + 1
        return {
            "population": self.population.size(),
            "teams": {k: len(v) for k, v in self._teams.items()},
            "tasks": by_status,
            "open": by_status.get("open", 0),
            "completed": by_status.get("completed", 0),
        }
