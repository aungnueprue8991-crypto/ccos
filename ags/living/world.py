"""XOR-lamp world: lamp ON iff switch_a XOR switch_b (hidden rule)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class XORLampWorld:
    switch_a: bool = False
    switch_b: bool = False
    step_count: int = 0

    def observe(self) -> Dict[str, Any]:
        self.step_count += 1
        lamp = self.switch_a ^ self.switch_b
        return {
            "switch_a": int(self.switch_a),
            "switch_b": int(self.switch_b),
            "lamp": int(lamp),
            "step": self.step_count,
        }

    def perform_action(self, action: str) -> Dict[str, Any]:
        if action == "TOGGLE_A":
            self.switch_a = not self.switch_a
        elif action == "TOGGLE_B":
            self.switch_b = not self.switch_b
        elif action == "WAIT":
            pass
        else:
            return {"ok": False, "error": f"unknown_action:{action}"}
        return {"ok": True, "observation": self.observe()}
