"""Multi-node ledger replication — append-only log sync with chain verification."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class NodeInfo:
    node_id: str
    name: str
    ledger_path: Path
    sequence: int = 0
    last_hash: Optional[str] = None


class ReplicationNode:
    def __init__(self, name: str, workspace: Path | str):
        self.node_id = str(uuid4())
        self.name = name
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.ledger = EventLedger(self.workspace / "events.db")
        self._lock = threading.RLock()

    def info(self) -> NodeInfo:
        events = list(self.ledger.iter_events())
        last = events[-1] if events else None
        return NodeInfo(
            node_id=self.node_id, name=self.name, ledger_path=self.ledger.path,
            sequence=self.ledger.count(), last_hash=last.payload_hash if last else None,
        )

    def append_local(self, event: EventEnvelope) -> EventEnvelope:
        return self.ledger.append(event)

    def export_from(self, sequence: int) -> List[dict]:
        out = []
        for ev in self.ledger.iter_events():
            if ev.sequence is not None and ev.sequence >= sequence:
                out.append(json.loads(ev.model_dump_json()))
        return out

    def import_events(self, raw_events: List[dict]) -> int:
        imported = 0
        with self._lock:
            for raw in raw_events:
                existing = self.ledger.get_by_id(raw.get("event_id", ""))
                if existing:
                    continue
                try:
                    ev = EventEnvelope.model_validate(raw)
                    new_ev = EventEnvelope(
                        event_type=ev.event_type, producer_id=ev.producer_id,
                        payload=ev.payload, correlation_id=ev.correlation_id,
                        causation_id=ev.causation_id, provenance=ev.provenance,
                        timestamp=ev.timestamp,
                    )
                    self.ledger.append(new_ev)
                    imported += 1
                except Exception:
                    continue
        return imported


class ReplicationCluster:
    def __init__(self):
        self.nodes: Dict[str, ReplicationNode] = {}
        self._lock = threading.RLock()

    def add_node(self, name: str, workspace: Path | str) -> ReplicationNode:
        node = ReplicationNode(name, workspace)
        with self._lock:
            self.nodes[node.node_id] = node
        return node

    def sync(self, source_id: str, target_id: str) -> dict:
        with self._lock:
            src = self.nodes[source_id]
            tgt = self.nodes[target_id]
        batch = src.export_from(0)
        imported = tgt.import_events(batch)
        tgt_ok = tgt.ledger.verify_chain()
        return {
            "source": src.name, "target": tgt.name,
            "exported": len(batch), "imported": imported,
            "target_chain_valid": tgt_ok, "target_count": tgt.ledger.count(),
        }

    def sync_all(self) -> List[dict]:
        results = []
        ids = list(self.nodes.keys())
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                results.append(self.sync(a, b))
                results.append(self.sync(b, a))
        return results

    def status(self) -> List[dict]:
        return [
            {"node_id": n.node_id, "name": n.name, "count": n.ledger.count(), "chain_valid": n.ledger.verify_chain()}
            for n in self.nodes.values()
        ]
