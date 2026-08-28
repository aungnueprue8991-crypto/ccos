"""World resource accounting."""

from __future__ import annotations

from typing import Dict


class ResourceLedger:
    def __init__(self, initial: Dict[str, float] | None = None):
        self.stocks: Dict[str, float] = dict(
            initial
            or {
                "energy": 1000.0,
                "matter": 500.0,
                "water": 200.0,
                "compute": 100.0,
            }
        )

    def can_spend(self, resource: str, amount: float) -> bool:
        return self.stocks.get(resource, 0) >= amount

    def spend(self, resource: str, amount: float) -> bool:
        if not self.can_spend(resource, amount):
            return False
        self.stocks[resource] = round(self.stocks[resource] - amount, 6)
        return True

    def add(self, resource: str, amount: float) -> None:
        self.stocks[resource] = round(self.stocks.get(resource, 0) + amount, 6)
