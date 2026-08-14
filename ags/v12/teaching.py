"""AGS v1.2 — Teaching + Provenance Hardening.

Epistemic rule:
  RECEIVED → UNVERIFIED → (PASS) VERIFIED | (FAIL) QUARANTINED
Memory ≠ belief. Knowledge ≠ verified knowledge.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts


def evidence_hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


class BeliefState(str, Enum):
    RECEIVED = "received"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


@dataclass
class KnowledgePacket:
    packet_id: str
    claim: str
    target: str
    model: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    evidence_hash: str
    discovery_id: str
    creator_id: str
    method: str
    confidence: float
    provenance: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=now_ts)
    skill_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        claim: str,
        target: str,
        model: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        creator_id: str,
        method: str = "linear_fit",
        confidence: float = 0.5,
        skill_hint: Optional[str] = None,
        discovery_id: Optional[str] = None,
    ) -> "KnowledgePacket":
        eh = evidence_hash(evidence)
        return cls(
            packet_id=new_id(),
            claim=claim,
            target=target,
            model=model,
            evidence=list(evidence),
            evidence_hash=eh,
            discovery_id=discovery_id or new_id(),
            creator_id=creator_id,
            method=method,
            confidence=confidence,
            provenance=[creator_id],
            skill_hint=skill_hint,
        )

    def integrity_ok(self) -> bool:
        return self.evidence_hash == evidence_hash(self.evidence)


@dataclass
class BeliefRecord:
    packet_id: str
    state: BeliefState
    packet: KnowledgePacket
    received_at: float = field(default_factory=now_ts)
    verified_at: Optional[float] = None
    proficiency_delta: float = 0.0


class SocialEpistemicMemory:
    """Private social memory with explicit belief states."""

    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        self.records: Dict[str, BeliefRecord] = {}
        self.skill_proficiency: Dict[str, float] = {}

    def receive(self, packet: KnowledgePacket) -> BeliefRecord:
        # Always start UNVERIFIED — never auto-believe
        state = BeliefState.UNVERIFIED if packet.integrity_ok() else BeliefState.QUARANTINED
        if not packet.integrity_ok():
            state = BeliefState.QUARANTINED
        rec = BeliefRecord(packet.packet_id, state, packet)
        # chain provenance
        packet.provenance = list(packet.provenance) + [self.owner_id]
        self.records[packet.packet_id] = rec
        return rec

    def mark_verified(self, packet_id: str) -> None:
        if packet_id in self.records:
            self.records[packet_id].state = BeliefState.VERIFIED
            self.records[packet_id].verified_at = now_ts()

    def mark_quarantined(self, packet_id: str) -> None:
        if packet_id in self.records:
            self.records[packet_id].state = BeliefState.QUARANTINED

    def verified_claims(self) -> List[KnowledgePacket]:
        return [r.packet for r in self.records.values() if r.state == BeliefState.VERIFIED]

    def unverified(self) -> List[KnowledgePacket]:
        return [r.packet for r in self.records.values() if r.state == BeliefState.UNVERIFIED]

    def practice_skill(self, skill: str, amount: float = 0.15) -> float:
        self.skill_proficiency[skill] = min(1.0, self.skill_proficiency.get(skill, 0.2) + amount)
        return self.skill_proficiency[skill]


class VerificationEngine:
    """Independent reproduction of a taught claim."""

    def verify_packet(self, packet: KnowledgePacket, fit_fn=None) -> bool:
        if not packet.integrity_ok():
            return False
        if fit_fn is None:
            # structural check: model has expected keys + low reported rmse
            rmse = float(packet.model.get("rmse", 99))
            return rmse <= 0.05 and "coeffs" in packet.model
        try:
            model = fit_fn(packet.evidence, packet.target, packet.model.get("inputs", []))
            return model is not None and float(model.get("rmse", 99)) <= 0.05
        except Exception:
            return False


class TeachingProtocol:
    def __init__(self, verification: Optional[VerificationEngine] = None):
        self.verification = verification or VerificationEngine()

    def teach(
        self,
        teacher_id: str,
        claim: str,
        target: str,
        model: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        confidence: float = 0.8,
        skill_hint: Optional[str] = "linear_relation_estimation",
    ) -> KnowledgePacket:
        return KnowledgePacket.create(
            claim=claim,
            target=target,
            model=model,
            evidence=evidence,
            creator_id=teacher_id,
            confidence=confidence,
            skill_hint=skill_hint,
        )

    def receive_and_evaluate(
        self,
        student_memory: SocialEpistemicMemory,
        packet: KnowledgePacket,
        fit_fn=None,
    ) -> BeliefState:
        rec = student_memory.receive(packet)
        if rec.state == BeliefState.QUARANTINED:
            return rec.state
        # Independent test
        ok = self.verification.verify_packet(packet, fit_fn=fit_fn)
        if ok:
            student_memory.mark_verified(packet.packet_id)
            if packet.skill_hint:
                delta = student_memory.practice_skill(packet.skill_hint, 0.2)
                rec.proficiency_delta = delta
            return BeliefState.VERIFIED
        student_memory.mark_quarantined(packet.packet_id)
        return BeliefState.QUARANTINED
