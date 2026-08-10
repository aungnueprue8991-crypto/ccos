"""Organization Registry — durable org + membership."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional

from constitution.schemas.citizen import Organization
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class OrganizationRegistry:
    def __init__(self, ledger: Optional[EventLedger] = None, db_path: Path | str = "storage/organizations.db"):
        self.ledger = ledger
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init()

    def _init(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS organizations (
                    org_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    members TEXT,
                    roles TEXT,
                    authority TEXT,
                    resources TEXT,
                    policies TEXT,
                    objectives TEXT,
                    raw_json TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def create(self, name: str, objectives: list[str] | None = None, policies: list[str] | None = None) -> Organization:
        org = Organization(
            name=name,
            objectives=objectives or [],
            policies=policies or [],
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO organizations VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    org.org_id, org.name, json.dumps(org.members), json.dumps(org.roles),
                    json.dumps(org.authority), json.dumps(org.resources),
                    json.dumps(org.policies), json.dumps(org.objectives), org.model_dump_json(),
                ),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="governance.org.created",
                    producer_id="governance.organizations",
                    payload={"org_id": org.org_id, "name": name},
                )
            )
        return org

    def add_member(self, org_id: str, citizen_or_agent_id: str, role: str = "member") -> Organization:
        org = self.get(org_id)
        if not org:
            raise KeyError(org_id)
        if citizen_or_agent_id not in org.members:
            org.members.append(citizen_or_agent_id)
        org.roles.setdefault(role, [])
        if citizen_or_agent_id not in org.roles[role]:
            org.roles[role].append(citizen_or_agent_id)
        with self._lock:
            self._conn.execute(
                "UPDATE organizations SET members=?, roles=?, raw_json=? WHERE org_id=?",
                (json.dumps(org.members), json.dumps(org.roles), org.model_dump_json(), org_id),
            )
            self._conn.commit()
        return org

    def get(self, org_id: str) -> Optional[Organization]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM organizations WHERE org_id = ?", (org_id,))
            row = cur.fetchone()
            return Organization.model_validate_json(row[0]) if row else None

    def get_by_name(self, name: str) -> Optional[Organization]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM organizations WHERE name = ?", (name,))
            row = cur.fetchone()
            return Organization.model_validate_json(row[0]) if row else None

    def list_all(self) -> List[Organization]:
        with self._lock:
            cur = self._conn.execute("SELECT raw_json FROM organizations")
            return [Organization.model_validate_json(r[0]) for r in cur.fetchall()]
