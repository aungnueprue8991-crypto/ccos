"""Production Capability Registry — lifecycle strictly controlled by constitution."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import List, Optional

from constitution.schemas.capability import CapabilityManifest, CapabilityLifecycle
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class CapabilityRegistry:
    def __init__(
        self,
        ledger: Optional[EventLedger] = None,
        db_path: Path | str = "storage/capabilities.db",
    ):
        self.ledger = ledger
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS capabilities (
                    capability_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    name TEXT NOT NULL,
                    lifecycle_status TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def register(self, manifest: CapabilityManifest) -> CapabilityManifest:
        if manifest.lifecycle_status == CapabilityLifecycle.DISCOVERED:
            manifest.lifecycle_status = CapabilityLifecycle.REGISTERED
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO capabilities
                (capability_id, version, name, lifecycle_status, manifest_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.capability_id,
                    manifest.version,
                    manifest.name,
                    manifest.lifecycle_status.value,
                    manifest.model_dump_json(),
                    manifest.created_at.isoformat(),
                ),
            )
            self._conn.commit()
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="capability.registered",
                    producer_id="cos.registry",
                    payload={
                        "capability_id": manifest.capability_id,
                        "name": manifest.name,
                        "version": manifest.version,
                        "lifecycle": manifest.lifecycle_status.value,
                    },
                )
            )
        return manifest

    def get(self, capability_id: str) -> Optional[CapabilityManifest]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT manifest_json FROM capabilities WHERE capability_id = ?",
                (capability_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return CapabilityManifest.model_validate_json(row[0])

    def list_by_status(self, status: CapabilityLifecycle) -> List[CapabilityManifest]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT manifest_json FROM capabilities WHERE lifecycle_status = ?",
                (status.value,),
            )
            return [CapabilityManifest.model_validate_json(r[0]) for r in cur.fetchall()]

    def list_active(self) -> List[CapabilityManifest]:
        return self.list_by_status(CapabilityLifecycle.ACTIVE)

    def transition(
        self,
        capability_id: str,
        new_status: CapabilityLifecycle,
        reason: str = "",
        authorized_by: str = "",
    ) -> CapabilityManifest:
        with self._lock:
            cap = self.get(capability_id)
            if cap is None:
                raise KeyError(f"Capability {capability_id} not found")
            old = cap.lifecycle_status

            if new_status == CapabilityLifecycle.ACTIVE:
                if old not in (
                    CapabilityLifecycle.APPROVED,
                    CapabilityLifecycle.VERIFIED,
                ):
                    raise PermissionError(
                        "CCOS-004: capability may not become ACTIVE without "
                        "verification + governance approval"
                    )
                if not authorized_by:
                    raise PermissionError(
                        "CCOS-001: ACTIVE transition requires authorized_by"
                    )

            cap.lifecycle_status = new_status
            self._conn.execute(
                "UPDATE capabilities SET lifecycle_status = ?, manifest_json = ? WHERE capability_id = ?",
                (new_status.value, cap.model_dump_json(), capability_id),
            )
            self._conn.commit()

        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="capability.lifecycle",
                    producer_id="cos.registry",
                    payload={
                        "capability_id": capability_id,
                        "from": old.value,
                        "to": new_status.value,
                        "reason": reason,
                        "authorized_by": authorized_by,
                    },
                )
            )
        return cap
