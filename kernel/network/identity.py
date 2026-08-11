"""N2.1 — Cryptographic node identity (stdlib HMAC-SHA256)."""

from __future__ import annotations
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class TrustState(str, Enum):
    UNKNOWN = "UNKNOWN"
    PROVISIONED = "PROVISIONED"
    TRUSTED = "TRUSTED"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"


class NodeIdentity(BaseModel):
    node_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "node"
    public_key: str = ""
    key_algorithm: str = "HMAC-SHA256"
    incarnation: int = 1
    trust_state: TrustState = TrustState.PROVISIONED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_config = {"extra": "forbid"}


class NodeKeyMaterial:
    def __init__(self, identity: NodeIdentity, secret: bytes):
        self.identity = identity
        self._secret = secret

    @classmethod
    def generate(cls, name: str = "node") -> "NodeKeyMaterial":
        secret = secrets.token_bytes(32)
        pub = hashlib.sha256(secret).hexdigest()
        identity = NodeIdentity(name=name, public_key=pub, key_algorithm="HMAC-SHA256")
        return cls(identity, secret)

    @classmethod
    def load(cls, path: Path) -> "NodeKeyMaterial":
        data = json.loads(Path(path).read_text())
        identity = NodeIdentity.model_validate(data["identity"])
        secret = bytes.fromhex(data["secret_hex"])
        return cls(identity, secret)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "identity": json.loads(self.identity.model_dump_json()),
            "secret_hex": self._secret.hex(),
        }, indent=2))

    def sign(self, message: bytes | str) -> str:
        if isinstance(message, str):
            message = message.encode("utf-8")
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()

    def verify(self, message: bytes | str, signature: str, public_key: Optional[str] = None) -> bool:
        if isinstance(message, str):
            message = message.encode("utf-8")
        expected = hmac.new(self._secret, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def public_identity(self) -> NodeIdentity:
        return self.identity.model_copy()


class PeerRegistry:
    def __init__(self):
        self._peers: dict[str, dict[str, Any]] = {}

    def add_peer(self, identity: NodeIdentity, verify_secret: bytes | None = None) -> None:
        self._peers[identity.node_id] = {
            "identity": identity, "verify_secret": verify_secret, "trust_state": identity.trust_state,
        }

    def get(self, node_id: str) -> Optional[dict]:
        return self._peers.get(node_id)

    def set_trust(self, node_id: str, state: TrustState) -> None:
        if node_id in self._peers:
            self._peers[node_id]["trust_state"] = state
            self._peers[node_id]["identity"].trust_state = state

    def verify_peer_signature(self, node_id: str, message: bytes | str, signature: str) -> bool:
        peer = self._peers.get(node_id)
        if not peer or peer.get("trust_state") == TrustState.REVOKED:
            return False
        secret = peer.get("verify_secret")
        if secret is None:
            return False
        if isinstance(message, str):
            message = message.encode("utf-8")
        expected = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def list_peers(self) -> list[NodeIdentity]:
        return [p["identity"] for p in self._peers.values()]
