"""N2 Network Fabric — signed, authenticated, verified replication."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger
from kernel.network.identity import NodeKeyMaterial, PeerRegistry, TrustState, NodeIdentity
from kernel.network.protocol import (
    ReplicationRequest, ReplicationResponse, ConflictAction, HeadInfo, classify_batch,
)


class NetworkNode:
    def __init__(self, name: str, workspace: Path | str, keys: Optional[NodeKeyMaterial] = None):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.keys = keys or NodeKeyMaterial.generate(name)
        self.identity = self.keys.identity
        self.identity.name = name
        self.ledger = EventLedger(self.workspace / "events.db")
        self.peers = PeerRegistry()
        self.quarantine: List[dict] = []
        self._lock = threading.RLock()
        self.keys.save(self.workspace / "node_identity.json")
        self.ledger.append(EventEnvelope(
            event_type="network.node.boot", producer_id=self.identity.node_id,
            payload={"node_id": self.identity.node_id, "name": name,
                     "public_key": self.identity.public_key, "algorithm": self.identity.key_algorithm},
        ))

    def head(self) -> HeadInfo:
        events = list(self.ledger.iter_events())
        last = events[-1] if events else None
        return HeadInfo(
            node_id=self.identity.node_id, name=self.identity.name,
            sequence=self.ledger.count(),
            last_hash=last.payload_hash if last else None,
            chain_valid=self.ledger.verify_chain(),
            public_key=self.identity.public_key,
            trust_state=self.identity.trust_state.value,
        )

    def provision_peer(self, peer: "NetworkNode") -> None:
        self.peers.add_peer(peer.identity.model_copy(), verify_secret=peer.keys._secret)
        peer.peers.add_peer(self.identity.model_copy(), verify_secret=self.keys._secret)
        self.ledger.append(EventEnvelope(
            event_type="network.peer.provisioned", producer_id=self.identity.node_id,
            payload={"peer_id": peer.identity.node_id, "peer_name": peer.identity.name},
        ))

    def append_local(self, event: EventEnvelope) -> EventEnvelope:
        return self.ledger.append(event)

    def build_push_request(self, receiver_id: str, from_sequence: int = 0) -> ReplicationRequest:
        batch = []
        for ev in self.ledger.iter_events():
            if ev.sequence is not None and ev.sequence >= from_sequence:
                batch.append(json.loads(ev.model_dump_json()))
        head = self.head()
        req = ReplicationRequest(
            sender_node=self.identity.node_id, receiver_node=receiver_id,
            from_sequence=from_sequence, to_sequence=head.sequence,
            event_batch=batch, previous_hash=head.last_hash,
        )
        req.signature = self.keys.sign(req.canonical_bytes())
        return req

    def handle_request(self, req: ReplicationRequest) -> ReplicationResponse:
        with self._lock:
            if not self.peers.verify_peer_signature(req.sender_node, req.canonical_bytes(), req.signature):
                self.ledger.append(EventEnvelope(
                    event_type="network.replication.rejected", producer_id=self.identity.node_id,
                    payload={"reason": "invalid_signature", "sender": req.sender_node, "request_id": req.request_id},
                ))
                return ReplicationResponse(
                    request_id=req.request_id, receiver_node=self.identity.node_id,
                    action=ConflictAction.REJECT, message="invalid signature or unknown peer",
                    rejected=len(req.event_batch), head_sequence=self.ledger.count(),
                )
            peer = self.peers.get(req.sender_node)
            if peer and peer.get("trust_state") in (TrustState.QUARANTINED, TrustState.REVOKED):
                return ReplicationResponse(
                    request_id=req.request_id, receiver_node=self.identity.node_id,
                    action=ConflictAction.REJECT, message=f"peer trust_state={peer['trust_state']}",
                    rejected=len(req.event_batch), head_sequence=self.ledger.count(),
                )
            head = self.head()
            action = classify_batch(head.sequence, head.last_hash, req.event_batch, req.from_sequence)
            if action == ConflictAction.REJECT:
                return ReplicationResponse(
                    request_id=req.request_id, receiver_node=self.identity.node_id,
                    action=action, message="invalid batch", rejected=len(req.event_batch),
                    head_sequence=head.sequence, head_hash=head.last_hash,
                )
            if action == ConflictAction.QUARANTINE:
                qid = str(uuid4())
                self.quarantine.append({"id": qid, "request": json.loads(req.model_dump_json())})
                self.peers.set_trust(req.sender_node, TrustState.QUARANTINED)
                self.ledger.append(EventEnvelope(
                    event_type="replication.conflict.detected", producer_id=self.identity.node_id,
                    payload={"quarantine_id": qid, "sender": req.sender_node, "reason": "divergent_hash"},
                ))
                return ReplicationResponse(
                    request_id=req.request_id, receiver_node=self.identity.node_id,
                    action=action, message="divergent history quarantined", quarantine_id=qid,
                    rejected=len(req.event_batch), head_sequence=head.sequence, head_hash=head.last_hash,
                )
            if action == ConflictAction.REQUEST_MISSING:
                return ReplicationResponse(
                    request_id=req.request_id, receiver_node=self.identity.node_id,
                    action=action, message="gap detected", missing_from=head.sequence,
                    head_sequence=head.sequence, head_hash=head.last_hash,
                )
            if action == ConflictAction.IDEMPOTENT_ACCEPT:
                return ReplicationResponse(
                    request_id=req.request_id, receiver_node=self.identity.node_id,
                    action=action, message="duplicates only", accepted=0,
                    head_sequence=head.sequence, head_hash=head.last_hash,
                    chain_valid=self.ledger.verify_chain(),
                )
            accepted = rejected = 0
            for raw in req.event_batch:
                existing = self.ledger.get_by_id(raw.get("event_id", ""))
                if existing:
                    accepted += 1
                    continue
                seq = raw.get("sequence")
                if seq is not None and seq < head.sequence:
                    accepted += 1
                    continue
                try:
                    ev = EventEnvelope(
                        event_type=raw["event_type"],
                        producer_id=raw.get("producer_id", req.sender_node),
                        payload=raw.get("payload") or {},
                        correlation_id=raw.get("correlation_id"),
                        causation_id=raw.get("causation_id"),
                        provenance=raw.get("provenance") or [],
                    )
                    self.ledger.append(ev)
                    accepted += 1
                except Exception:
                    rejected += 1
            ok = self.ledger.verify_chain()
            self.ledger.append(EventEnvelope(
                event_type="network.replication.applied", producer_id=self.identity.node_id,
                payload={"request_id": req.request_id, "sender": req.sender_node,
                         "accepted": accepted, "rejected": rejected, "chain_valid": ok},
            ))
            new_head = self.head()
            return ReplicationResponse(
                request_id=req.request_id, receiver_node=self.identity.node_id,
                action=ConflictAction.APPEND, accepted=accepted, rejected=rejected,
                message="appended", chain_valid=ok,
                head_sequence=new_head.sequence, head_hash=new_head.last_hash,
            )


class NetworkFabric:
    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}

    def create_node(self, name: str, workspace: Path | str) -> NetworkNode:
        node = NetworkNode(name, workspace)
        self.nodes[node.identity.node_id] = node
        return node

    def provision_mesh(self, nodes: List[NetworkNode]) -> None:
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                a.provision_peer(b)

    def sync(self, source_id: str, target_id: str, from_sequence: int = 0) -> ReplicationResponse:
        src = self.nodes[source_id]
        tgt = self.nodes[target_id]
        req = src.build_push_request(target_id, from_sequence=from_sequence)
        return tgt.handle_request(req)

    def status(self) -> list[dict]:
        return [{
            "node_id": n.identity.node_id, "name": n.identity.name,
            "head": n.head().model_dump(), "peers": len(n.peers.list_peers()),
            "quarantine": len(n.quarantine),
        } for n in self.nodes.values()]
