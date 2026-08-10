"""N5 CivilizationInstance — one sovereign CCOS civilization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from constitution.schemas.federation import (
    CivilizationIdentity, CivTrustState, FederationTreaty, EvidencePackage,
)
from constitution.schemas.event import EventEnvelope
from hermes.shell import Hermes
from kernel.network.identity import NodeKeyMaterial


class CivilizationInstance:
    def __init__(self, name: str, workspace: Path | str):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.hermes = Hermes(self.workspace)
        self.keys = NodeKeyMaterial.generate(name)
        constitution_blob = json.dumps(
            {"version": getattr(self.hermes.cfg, "constitution_version", "1.0.0"), "name": name},
            sort_keys=True,
        )
        self.identity = CivilizationIdentity(
            name=name,
            root_identity=self.keys.identity.public_key,
            constitution_hash=hashlib.sha256(constitution_blob.encode()).hexdigest()[:32],
            public_keys={"root": self.keys.identity.public_key},
            federation_policy={
                "admit": "attested", "share_knowledge": True, "share_capability": True,
                "joint_experiment": True, "max_trust": CivTrustState.TRUSTED_PARTNER.value,
            },
            provenance=["genesis", name],
        )
        self.peers: Dict[str, dict] = {}
        self.treaties: Dict[str, FederationTreaty] = {}
        self.evidence_inbox: List[EvidencePackage] = []
        self.knowledge_accepted: List[dict] = []
        self.capability_offers: Dict[str, dict] = {}
        self.joint_experiments: Dict[str, dict] = {}
        self._seen_nonces: set[str] = set()
        self.hermes.ledger.append(EventEnvelope(
            event_type="federation.civilization.boot",
            producer_id=self.identity.civilization_id,
            payload={"civilization_id": self.identity.civilization_id, "name": name,
                     "constitution_hash": self.identity.constitution_hash},
        ))

    def sign(self, message: str | bytes) -> str:
        return self.keys.sign(message)

    def _emit(self, event_type: str, payload: dict) -> None:
        self.hermes.ledger.append(EventEnvelope(
            event_type=event_type, producer_id=self.identity.civilization_id, payload=payload,
        ))
