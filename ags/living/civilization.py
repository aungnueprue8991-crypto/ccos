"""Civilization — multi-agent living population with governed reproduction."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ags.living.agent import LivingAgent
from ags.living.genome import load_default
from ags.living.governance import LivingReproductionGate
from ags.living.world import XORLampWorld

log = logging.getLogger("ags.living.civ")


class Civilization:
    def __init__(
        self,
        initial_agents: int = 1,
        max_population: int = 8,
        genome_path: Optional[str] = None,
        gate: Optional[LivingReproductionGate] = None,
    ):
        self.world = XORLampWorld()
        self.gate = gate or LivingReproductionGate()
        self.max_population = max_population
        self.agents: Dict[str, LivingAgent] = {}
        self._next = 0
        self._births: list = []
        for _ in range(initial_agents):
            self.spawn(load_default(genome_path))

    def spawn(self, genome: Dict[str, Any]) -> str:
        if len(self.agents) >= self.max_population:
            raise RuntimeError("max_population")
        self._next += 1
        aid = f"LIV-{self._next:04d}"
        agent = LivingAgent(aid, genome, self.world, ccos=self.gate)
        self.agents[aid] = agent
        return aid

    def tick(self) -> Dict[str, Any]:
        results = []
        for agent in list(self.agents.values()):
            r = agent.run_cycle()
            results.append(r)
            if "reproduction_drive" in r.get("events", []):
                decision = agent.request_reproduction()
                if decision.get("approved") and decision.get("child_genome"):
                    if len(self.agents) < self.max_population:
                        child_id = self.spawn(decision["child_genome"])
                        agent.state.offspring_count += 1
                        self._births.append({
                            "parent": agent.id,
                            "child": child_id,
                            "reason": decision.get("reason"),
                        })
        return {
            "population": len(self.agents),
            "results": results,
            "births_total": len(self._births),
            "last_births": self._births[-3:],
        }

    def run(self, cycles: int = 15) -> Dict[str, Any]:
        history = []
        for _ in range(cycles):
            history.append(self.tick())
        return {
            "final_population": len(self.agents),
            "births": self._births,
            "agents": {
                aid: {
                    "lifecycle": a.state.lifecycle,
                    "discoveries": a.state.discoveries,
                    "rule": a.state.known_rule,
                    "offspring": a.state.offspring_count,
                    "genome_id": a.genome.get("genome_id"),
                }
                for aid, a in self.agents.items()
            },
            "history_tail": history[-5:],
        }


def run_living_demo(cycles: int = 15) -> Dict[str, Any]:
    civ = Civilization(initial_agents=1, max_population=8)
    report = civ.run(cycles=cycles)
    print("Living civilization demo")
    print("population=", report["final_population"], "births=", len(report["births"]))
    for aid, info in report["agents"].items():
        print(f"  {aid}: {info}")
    return report
