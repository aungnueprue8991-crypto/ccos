"""Provenance for world experiments and scientific artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ags.shared.types import new_id, now_ts


@dataclass
class ProvenanceRecord:
    record_id: str
    kind: str
    parent_hash: str
    result_hash: str
    engine_version: str
    seed: int
    agent_id: str = ""
    experiment_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=now_ts)


class ProvenanceStore:
    def __init__(self):
        self.records: List[ProvenanceRecord] = []

    def add(
        self,
        kind: str,
        parent_hash: str,
        result_hash: str,
        engine_version: str,
        seed: int,
        **meta,
    ) -> ProvenanceRecord:
        rec = ProvenanceRecord(
            new_id(),
            kind,
            parent_hash,
            result_hash,
            engine_version,
            seed,
            agent_id=meta.pop("agent_id", ""),
            experiment_id=meta.pop("experiment_id", ""),
            metadata=meta,
        )
        self.records.append(rec)
        return rec

    def chain_valid(self) -> bool:
        return len(self.records) == len({r.record_id for r in self.records})
