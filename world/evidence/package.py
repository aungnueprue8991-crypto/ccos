"""WorldEvidencePackage — bridge from World Engine to CCOS epistemic layer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from ags.shared.types import new_id, now_ts


def _h(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


@dataclass
class WorldEvidencePackage:
    evidence_id: str
    world_id: str
    experiment_id: str
    initial_state_hash: str
    final_state_hash: str
    parent_state_hash: Optional[str]
    tick_start: int
    tick_end: int
    random_seed: int
    action_stream_hash: str
    hypothesis: str
    prediction: Dict[str, Any]
    observations: List[Dict[str, Any]]
    measurements: List[Dict[str, Any]]
    instruments: List[str]
    adapter_versions: Dict[str, str]
    numerical_precision: str
    uncertainty: Dict[str, Any]
    provenance_chain: List[str]
    replay_manifest: Dict[str, Any]
    evidence_hash: str = ""
    timestamp: float = field(default_factory=now_ts)

    def compute_hash(self) -> str:
        payload = asdict(self)
        payload.pop("evidence_hash", None)
        self.evidence_hash = _h(payload)
        return self.evidence_hash

    def to_dict(self) -> Dict[str, Any]:
        if not self.evidence_hash:
            self.compute_hash()
        return asdict(self)

    def verify_integrity(self) -> bool:
        current = self.evidence_hash
        recomputed = self.compute_hash()
        ok = current == recomputed
        self.evidence_hash = current or recomputed
        return ok


class EvidenceBuilder:
    def __init__(self, world_id: str, seed: int):
        self.world_id = world_id
        self.seed = seed
        self.actions: List[Dict[str, Any]] = []
        self.provenance: List[str] = []

    def record_action(self, action: Dict[str, Any]) -> None:
        self.actions.append(action)
        self.provenance.append(_h(action))

    def build(
        self,
        *,
        experiment_id: str,
        initial_state_hash: str,
        final_state_hash: str,
        parent_state_hash: Optional[str],
        tick_start: int,
        tick_end: int,
        hypothesis: str,
        prediction: Dict[str, Any],
        observations: List[Dict[str, Any]],
        measurements: List[Dict[str, Any]],
        instruments: List[str],
        adapter_versions: Optional[Dict[str, str]] = None,
        uncertainty: Optional[Dict[str, Any]] = None,
        numerical_precision: str = "float64_quantized_6",
    ) -> WorldEvidencePackage:
        action_stream_hash = _h(self.actions)
        pkg = WorldEvidencePackage(
            evidence_id=new_id(),
            world_id=self.world_id,
            experiment_id=experiment_id,
            initial_state_hash=initial_state_hash,
            final_state_hash=final_state_hash,
            parent_state_hash=parent_state_hash,
            tick_start=tick_start,
            tick_end=tick_end,
            random_seed=self.seed,
            action_stream_hash=action_stream_hash,
            hypothesis=hypothesis,
            prediction=prediction,
            observations=observations,
            measurements=measurements,
            instruments=instruments,
            adapter_versions=adapter_versions or {"thermodynamics": "0.1.0", "ecs": "0.1.0"},
            numerical_precision=numerical_precision,
            uncertainty=uncertainty or {},
            provenance_chain=list(self.provenance),
            replay_manifest={
                "seed": self.seed,
                "tick_start": tick_start,
                "tick_end": tick_end,
                "actions": len(self.actions),
            },
        )
        pkg.compute_hash()
        return pkg
