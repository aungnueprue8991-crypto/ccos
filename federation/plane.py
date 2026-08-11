"""N5 FederationPlane — sovereignty preserved."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from constitution.schemas.federation import (
    CivilizationIdentity, CivTrustState, FederationOp,
    FederationTreaty, FederationRequest, FederationResponse, EvidencePackage,
)
from constitution.schemas.event import EventEnvelope
from federation.civilization import CivilizationInstance


class FederationPlane:
    def __init__(self):
        self.civilizations: Dict[str, CivilizationInstance] = {}

    def spawn(self, name: str, workspace: Path | str) -> CivilizationInstance:
        civ = CivilizationInstance(name, workspace)
        self.civilizations[civ.identity.civilization_id] = civ
        return civ

    def discover(self, from_id: str, to_id: str) -> FederationResponse:
        sender = self.civilizations[from_id]
        receiver = self.civilizations[to_id]
        req = FederationRequest(
            sender_civilization=from_id, receiver_civilization=to_id,
            request_type=FederationOp.DISCOVER, intent="discover peer civilization",
            payload={"identity": json.loads(sender.identity.model_dump_json())},
        )
        req.signature = sender.sign(req.model_dump_json(exclude={"signature"}))
        return self._handle(receiver, req, sender)

    def attest(self, from_id: str, to_id: str) -> FederationResponse:
        sender = self.civilizations[from_id]
        receiver = self.civilizations[to_id]
        req = FederationRequest(
            sender_civilization=from_id, receiver_civilization=to_id,
            request_type=FederationOp.ATTEST, intent="cryptographic attestation",
            payload={"public_key": sender.keys.identity.public_key,
                     "constitution_hash": sender.identity.constitution_hash,
                     "node_id": sender.keys.identity.node_id},
        )
        req.signature = sender.sign(req.model_dump_json(exclude={"signature"}))
        return self._handle(receiver, req, sender)

    def _handle(self, receiver, req, sender) -> FederationResponse:
        if req.nonce in receiver._seen_nonces:
            receiver._emit("federation.rejected", {"reason": "replay", "request_id": req.request_id})
            return FederationResponse(request_id=req.request_id, decision="DENIED", message="replay detected")
        receiver._seen_nonces.add(req.nonce)

        if req.request_type == FederationOp.DISCOVER:
            receiver.peers[req.sender_civilization] = {
                "identity": CivilizationIdentity.model_validate(req.payload["identity"]),
                "trust": CivTrustState.DISCOVERED, "verify_secret": None,
            }
            receiver._emit("federation.discovered", {"peer": req.sender_civilization})
            return FederationResponse(request_id=req.request_id, decision="GRANTED",
                                      granted_scope=["discover"], message="discovered")

        if req.request_type == FederationOp.ATTEST:
            receiver.peers.setdefault(req.sender_civilization, {})
            receiver.peers[req.sender_civilization].update({
                "identity": receiver.peers.get(req.sender_civilization, {}).get("identity")
                    or CivilizationIdentity(
                        civilization_id=req.sender_civilization, name="peer",
                        constitution_hash=req.payload.get("constitution_hash", ""),
                        public_keys={"root": req.payload.get("public_key", "")},
                    ),
                "trust": CivTrustState.ATTESTED,
                "verify_secret": sender.keys._secret,
            })
            sender.peers.setdefault(receiver.identity.civilization_id, {})
            sender.peers[receiver.identity.civilization_id].update({
                "identity": receiver.identity, "trust": CivTrustState.ATTESTED,
                "verify_secret": receiver.keys._secret,
            })
            receiver._emit("federation.attested", {"peer": req.sender_civilization})
            return FederationResponse(request_id=req.request_id, decision="GRANTED",
                                      granted_scope=["attest"], message="attested")

        if req.request_type == FederationOp.NEGOTIATE:
            return self._negotiate(receiver, req, sender)
        if req.request_type == FederationOp.SHARE_KNOWLEDGE:
            return self._share_knowledge(receiver, req, sender)
        if req.request_type == FederationOp.SHARE_CAPABILITY:
            return self._share_capability(receiver, req, sender)
        if req.request_type == FederationOp.JOINT_EXPERIMENT:
            return FederationResponse(request_id=req.request_id, decision="GRANTED",
                                      message="use plane.joint_experiment")
        if req.request_type == FederationOp.REVOKE:
            return self._revoke(receiver, req)
        return FederationResponse(request_id=req.request_id, decision="DENIED", message="unknown op")

    def negotiate_treaty(self, a_id: str, b_id: str, scope: str = "research",
                         permissions: Optional[list] = None) -> FederationTreaty:
        a, b = self.civilizations[a_id], self.civilizations[b_id]
        treaty = FederationTreaty(
            parties=[a_id, b_id], scope=scope,
            permissions=permissions or ["SHARE_KNOWLEDGE", "SHARE_CAPABILITY", "JOINT_EXPERIMENT"],
            obligations=["respect_sovereignty", "provenance_required", "no_remote_mutation"],
            data_rules={"evidence_only": True, "no_forced_belief": True},
            capability_rules={"local_lifecycle_only": True},
            experiment_rules={"independent_verify": True},
        )
        treaty.signatures[a_id] = a.sign(treaty.treaty_id + scope)
        treaty.signatures[b_id] = b.sign(treaty.treaty_id + scope)
        treaty.status = "active"
        a.treaties[treaty.treaty_id] = treaty
        b.treaties[treaty.treaty_id] = treaty
        if a_id in b.peers:
            b.peers[a_id]["trust"] = CivTrustState.FEDERATED
        if b_id in a.peers:
            a.peers[b_id]["trust"] = CivTrustState.FEDERATED
        a._emit("federation.treaty.active", {"treaty_id": treaty.treaty_id, "parties": treaty.parties})
        b._emit("federation.treaty.active", {"treaty_id": treaty.treaty_id, "parties": treaty.parties})
        return treaty

    def _negotiate(self, receiver, req, sender) -> FederationResponse:
        treaty = self.negotiate_treaty(req.sender_civilization, receiver.identity.civilization_id)
        return FederationResponse(request_id=req.request_id, decision="GRANTED",
                                  granted_scope=treaty.permissions, message=f"treaty {treaty.treaty_id}")

    def share_knowledge(self, from_id: str, to_id: str, claims: list[str], evidence_refs: list[str],
                        methodology: str = "experiment", metrics: Optional[dict] = None) -> FederationResponse:
        sender, receiver = self.civilizations[from_id], self.civilizations[to_id]
        pkg = EvidencePackage(
            source_civilization=from_id, claims=claims, evidence_refs=evidence_refs,
            methodology=methodology, metrics=metrics or {}, provenance=[from_id] + evidence_refs,
        )
        pkg.signature = sender.sign(pkg.model_dump_json(exclude={"signature"}))
        req = FederationRequest(
            sender_civilization=from_id, receiver_civilization=to_id,
            request_type=FederationOp.SHARE_KNOWLEDGE, intent="share evidence package",
            payload=json.loads(pkg.model_dump_json()), provenance=pkg.provenance,
        )
        req.signature = sender.sign(req.model_dump_json(exclude={"signature"}))
        return self._handle(receiver, req, sender)

    def _share_knowledge(self, receiver, req, sender) -> FederationResponse:
        pkg = EvidencePackage.model_validate(req.payload)
        receiver.evidence_inbox.append(pkg)
        accepted = False
        if pkg.provenance and pkg.signature and pkg.claims:
            for claim in pkg.claims:
                receiver.hermes.evidence.ingest_observation(claim, source=f"federation:{pkg.source_civilization}")
            accepted = True
            receiver.knowledge_accepted.append({
                "package_id": pkg.package_id, "claims": pkg.claims,
                "status": "UNVERIFIED_EXTERNAL", "source": pkg.source_civilization,
            })
        receiver._emit("federation.knowledge.received", {
            "package_id": pkg.package_id, "from": pkg.source_civilization,
            "claims": len(pkg.claims), "auto_believed": False,
        })
        return FederationResponse(
            request_id=req.request_id, decision="GRANTED" if accepted else "DENIED",
            granted_scope=["evidence_receive"],
            message="evidence accepted for local evaluation; not auto-believed",
            constraints={"auto_believe": False},
        )

    def share_capability(self, from_id: str, to_id: str, capability_name: str,
                         manifest_summary: dict) -> FederationResponse:
        sender, receiver = self.civilizations[from_id], self.civilizations[to_id]
        req = FederationRequest(
            sender_civilization=from_id, receiver_civilization=to_id,
            request_type=FederationOp.SHARE_CAPABILITY,
            intent=f"offer capability {capability_name}",
            capabilities_requested=[capability_name],
            payload={"manifest": manifest_summary, "name": capability_name},
        )
        req.signature = sender.sign(req.model_dump_json(exclude={"signature"}))
        return self._handle(receiver, req, sender)

    def _share_capability(self, receiver, req, sender) -> FederationResponse:
        name = req.payload.get("name", "remote")
        receiver.capability_offers[name] = {
            "from": req.sender_civilization, "manifest": req.payload.get("manifest"),
            "local_status": "DISCOVERED", "remote_claimed": "ACTIVE",
        }
        receiver._emit("federation.capability.offered", {
            "name": name, "from": req.sender_civilization, "local_status": "DISCOVERED",
            "note": "remote ACTIVE does not imply local ACTIVE",
        })
        return FederationResponse(
            request_id=req.request_id, decision="GRANTED", granted_scope=["capability_offer"],
            message="offer recorded as DISCOVERED locally",
            constraints={"local_lifecycle": "DISCOVERED", "no_auto_active": True},
        )

    def joint_experiment(self, leader_id: str, partner_ids: list[str], hypothesis: str,
                         evaluate_fn: Callable[[dict], dict[str, float]],
                         change: Optional[dict] = None) -> dict:
        leader = self.civilizations[leader_id]
        local = leader.hermes.n4.run_full_cycle(
            target="federated-planner", hypothesis=hypothesis,
            change=change or {"boost": 0.12}, evaluate_fn=evaluate_fn, auto_promote=False,
        )
        partner_results = []
        for pid in partner_ids:
            partner = self.civilizations[pid]
            prepl = partner.hermes.n4.run_full_cycle(
                target="federated-planner", hypothesis=f"[replica] {hypothesis}",
                change=change or {"boost": 0.12}, evaluate_fn=evaluate_fn, auto_promote=False,
            )
            partner_results.append({"civilization": pid, "result": prepl})
            partner._emit("federation.joint_experiment.replica", {
                "leader": leader_id, "status": prepl["status"], "verified": prepl.get("verified"),
            })
        synthesis = {
            "leader": local, "partners": partner_results,
            "all_verified": local.get("verified") and all(p["result"].get("verified") for p in partner_results),
            "hypothesis": hypothesis,
        }
        leader.joint_experiments[local["experiment_id"]] = synthesis
        leader._emit("federation.joint_experiment.completed", {
            "experiment_id": local["experiment_id"], "partners": partner_ids,
            "all_verified": synthesis["all_verified"],
        })
        return synthesis

    def revoke(self, from_id: str, to_id: str, reason: str = "policy") -> FederationResponse:
        sender, receiver = self.civilizations[from_id], self.civilizations[to_id]
        req = FederationRequest(
            sender_civilization=from_id, receiver_civilization=to_id,
            request_type=FederationOp.REVOKE, intent=reason,
        )
        req.signature = sender.sign(req.model_dump_json(exclude={"signature"}))
        return self._handle(receiver, req, sender)

    def _revoke(self, receiver, req) -> FederationResponse:
        peer_id = req.sender_civilization
        if peer_id in receiver.peers:
            receiver.peers[peer_id]["trust"] = CivTrustState.REVOKED
        for tid, t in list(receiver.treaties.items()):
            if peer_id in t.parties:
                t.status = "revoked"
                t.revocation = req.intent
        receiver._emit("federation.revoked", {"peer": peer_id, "reason": req.intent})
        return FederationResponse(request_id=req.request_id, decision="GRANTED", message="revoked")

    def assert_sovereignty(self) -> None:
        for cid, civ in self.civilizations.items():
            for ev in civ.hermes.ledger.find_by_type("capability.lifecycle"):
                if (ev.payload or {}).get("to") == "ACTIVE":
                    auth = (ev.payload or {}).get("authorized_by", "")
                    for other_id, other in self.civilizations.items():
                        if other_id != cid and other_id in str(auth):
                            raise AssertionError(
                                f"SOVEREIGNTY VIOLATION: {other.identity.name} activated on {civ.identity.name}"
                            )

    def status(self) -> list[dict]:
        out = []
        for cid, civ in self.civilizations.items():
            out.append({
                "civilization_id": cid, "name": civ.identity.name,
                "constitution_hash": civ.identity.constitution_hash,
                "peers": {
                    pid: (p.get("trust").value if hasattr(p.get("trust"), "value") else p.get("trust"))
                    for pid, p in civ.peers.items()
                },
                "treaties": len([t for t in civ.treaties.values() if t.status == "active"]),
                "evidence_inbox": len(civ.evidence_inbox),
                "capability_offers": len(civ.capability_offers),
                "chain_valid": civ.hermes.ledger.verify_chain(),
            })
        return out
