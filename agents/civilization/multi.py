"""Multi-civilization coordination — isolated Hermes instances + contracts."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class CivContract:
    contract_id: str = field(default_factory=lambda: str(uuid4()))
    from_civ: str = ""
    to_civ: str = ""
    offer: str = ""
    status: str = "proposed"
    evidence_refs: List[str] = field(default_factory=list)


class MultiCivilizationCoordinator:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.civs: Dict[str, object] = {}
        self.contracts: Dict[str, CivContract] = {}
        self._ledgers: Dict[str, EventLedger] = {}

    def spawn(self, name: str):
        from hermes.shell import Hermes
        ws = self.root / name
        ws.mkdir(parents=True, exist_ok=True)
        h = Hermes(ws)
        self.civs[name] = h
        self._ledgers[name] = h.ledger
        h.civilization.bootstrap_civilization(name)
        h.ledger.append(EventEnvelope(
            event_type="multiciv.spawned", producer_id="agents.multiciv",
            payload={"name": name, "workspace": str(ws)},
        ))
        return h

    def propose_contract(self, from_civ: str, to_civ: str, offer: str, evidence_refs: list[str] | None = None) -> CivContract:
        if from_civ not in self.civs or to_civ not in self.civs:
            raise KeyError("unknown civilization")
        c = CivContract(from_civ=from_civ, to_civ=to_civ, offer=offer, evidence_refs=evidence_refs or [])
        self.contracts[c.contract_id] = c
        for name in (from_civ, to_civ):
            self._ledgers[name].append(EventEnvelope(
                event_type="multiciv.contract.proposed", producer_id="agents.multiciv",
                payload={"contract_id": c.contract_id, "from": from_civ, "to": to_civ, "offer": offer},
            ))
        return c

    def accept_contract(self, contract_id: str, by_civ: str) -> CivContract:
        c = self.contracts[contract_id]
        if by_civ != c.to_civ:
            raise PermissionError("only target civ may accept")
        c.status = "accepted"
        for name in (c.from_civ, c.to_civ):
            self._ledgers[name].append(EventEnvelope(
                event_type="multiciv.contract.accepted", producer_id="agents.multiciv",
                payload={"contract_id": contract_id, "by": by_civ},
            ))
        return c

    def status(self) -> dict:
        return {
            "civilizations": list(self.civs.keys()),
            "contracts": {cid: {"from": c.from_civ, "to": c.to_civ, "status": c.status, "offer": c.offer}
                          for cid, c in self.contracts.items()},
            "chains_valid": {n: self._ledgers[n].verify_chain() for n in self.civs},
        }
