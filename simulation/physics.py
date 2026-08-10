"""Enhanced Artificial Cosmos with simple Newtonian-like dynamics."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class Body:
    body_id: str
    mass: float
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    energy: float = 100.0
    kind: str = "body"


class PhysicsCosmos:
    """2D particle simulation with gravity-lite for SCOS experiments."""

    def __init__(self, ledger: Optional[EventLedger] = None, seed: int = 42, G: float = 0.1):
        self.ledger = ledger
        self.rng = random.Random(seed)
        self.G = G
        self.bodies: List[Body] = []
        self.tick_n = 0
        self.cosmos_id = str(uuid4())
        self.dt = 0.1

    def spawn(self, mass: float = 1.0, kind: str = "body", **kwargs) -> Body:
        b = Body(
            body_id=str(uuid4()), mass=mass,
            x=kwargs.get("x", self.rng.uniform(0, 100)),
            y=kwargs.get("y", self.rng.uniform(0, 100)),
            vx=kwargs.get("vx", self.rng.uniform(-1, 1)),
            vy=kwargs.get("vy", self.rng.uniform(-1, 1)),
            energy=kwargs.get("energy", 100.0), kind=kind,
        )
        self.bodies.append(b)
        return b

    def _forces(self) -> Dict[str, Tuple[float, float]]:
        forces = {b.body_id: (0.0, 0.0) for b in self.bodies}
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = self.bodies[i], self.bodies[j]
                dx, dy = b.x - a.x, b.y - a.y
                dist = math.sqrt(dx * dx + dy * dy) + 1e-6
                f = self.G * a.mass * b.mass / (dist * dist)
                fx, fy = f * dx / dist, f * dy / dist
                ax, ay = forces[a.body_id]
                bx, by = forces[b.body_id]
                forces[a.body_id] = (ax + fx, ay + fy)
                forces[b.body_id] = (bx - fx, by - fy)
        return forces

    def tick(self, n: int = 1) -> dict:
        for _ in range(n):
            self.tick_n += 1
            forces = self._forces()
            for b in self.bodies:
                fx, fy = forces[b.body_id]
                ax, ay = fx / b.mass, fy / b.mass
                b.vx += ax * self.dt
                b.vy += ay * self.dt
                b.x += b.vx * self.dt
                b.y += b.vy * self.dt
                if b.x < 0 or b.x > 100:
                    b.vx *= -0.9
                    b.x = max(0, min(100, b.x))
                if b.y < 0 or b.y > 100:
                    b.vy *= -0.9
                    b.y = max(0, min(100, b.y))
                b.energy = max(0.0, b.energy - 0.01)
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="simulation.physics.tick", producer_id="simulation.physics",
                payload={"cosmos_id": self.cosmos_id, "tick": self.tick_n,
                         "n_bodies": len(self.bodies), "mean_energy": self.measure()["mean_energy"]},
            ))
        return self.measure()

    def measure(self) -> Dict[str, float]:
        if not self.bodies:
            return {"n_bodies": 0.0, "mean_energy": 0.0, "mean_speed": 0.0, "tick": float(self.tick_n)}
        energies = [b.energy for b in self.bodies]
        speeds = [math.sqrt(b.vx**2 + b.vy**2) for b in self.bodies]
        return {
            "n_bodies": float(len(self.bodies)),
            "mean_energy": sum(energies) / len(energies),
            "mean_speed": sum(speeds) / len(speeds),
            "tick": float(self.tick_n),
        }
