"""Artificial Cosmos — controlled simulation environments for SCOS experiments."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class Entity:
    entity_id: str
    kind: str
    energy: float = 100.0
    position: tuple[float, float] = (0.0, 0.0)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CosmosState:
    tick: int = 0
    entities: List[Entity] = field(default_factory=list)
    resources: float = 1000.0
    rules: Dict[str, Any] = field(default_factory=dict)


class ArtificialCosmos:
    """Minimal but real physics-free simulation world for capability experiments."""

    def __init__(self, ledger: Optional[EventLedger] = None, seed: int = 42):
        self.ledger = ledger
        self.rng = random.Random(seed)
        self.state = CosmosState(rules={"max_entities": 100, "energy_decay": 0.01})
        self.cosmos_id = str(uuid4())

    def spawn(self, kind: str, energy: float = 100.0, **props) -> Entity:
        e = Entity(
            entity_id=str(uuid4()),
            kind=kind,
            energy=energy,
            position=(self.rng.random() * 100, self.rng.random() * 100),
            properties=props,
        )
        if len(self.state.entities) >= self.state.rules.get("max_entities", 100):
            raise RuntimeError("cosmos capacity exceeded")
        self.state.entities.append(e)
        return e

    def tick(self, n: int = 1) -> CosmosState:
        for _ in range(n):
            self.state.tick += 1
            decay = self.state.rules.get("energy_decay", 0.01)
            for e in self.state.entities:
                e.energy = max(0.0, e.energy * (1.0 - decay))
            alive = [e for e in self.state.entities if e.energy > 1.0]
            self.state.entities = alive
            self.state.resources = max(0.0, self.state.resources - 0.1 * len(alive))
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="simulation.cosmos.tick",
                    producer_id="simulation.cosmos",
                    payload={
                        "cosmos_id": self.cosmos_id,
                        "tick": self.state.tick,
                        "n_entities": len(self.state.entities),
                        "resources": self.state.resources,
                    },
                )
            )
        return self.state

    def measure(self) -> Dict[str, float]:
        energies = [e.energy for e in self.state.entities] or [0.0]
        return {
            "n_entities": float(len(self.state.entities)),
            "mean_energy": sum(energies) / len(energies),
            "resources": self.state.resources,
            "tick": float(self.state.tick),
        }
