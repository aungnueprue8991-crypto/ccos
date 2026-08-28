"""World Engine v1.6 — Reproducible Scientific Civilization Loop (E2E)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from world.core.world import World
from world.core.entity import Transform, Mass, Energy, Label
from world.laboratory.fork import Laboratory
from world.governance.bridge import WorldCapabilityBridge
from world.adapters.thermodynamics import ThermodynamicsAdapter, ThermalBody
from world.evidence.package import EvidenceBuilder, WorldEvidencePackage
from world.provenance.record import ProvenanceStore
from world.replay.engine import ReplayEngine
from world.science.oracle import ThermoEquilibriumOracle


@dataclass
class CivilizationLoopResult:
    success: bool
    evidence: Optional[WorldEvidencePackage]
    discovery: Optional[str]
    live_hash_before: str
    live_hash_after: str
    fork_hash: str
    ledger_events: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""


class ScientificCivilizationLoop:
    """intent → governance → observe → experiment → evidence → oracle → ledger"""

    def __init__(self, seed: int = 42, strict: bool = False, ccos: Any = None):
        self.seed = seed
        self.strict = strict
        self.world = World(seed=seed, name="civ-loop")
        self.world.spawn(
            Label("lab-bench", "apparatus"),
            Transform(0, 0, 0),
            Mass(10.0),
            Energy(100.0),
        )
        self.world.spawn(
            Label("sample", "object"),
            Transform(1, 0, 0),
            Mass(1.0),
            Energy(50.0),
        )
        self.bridge = WorldCapabilityBridge(self.world, ccos=ccos, strict=strict)
        self.lab = Laboratory(self.world)
        self.provenance = ProvenanceStore()
        self.replay = ReplayEngine()
        self.ledger: List[Dict[str, Any]] = []
        self.knowledge: List[str] = []
        self._ccos = ccos

    def _grant_scientist(self, agent_id: str) -> None:
        caps = ("world.observe", "world.experiment", "world.fork", "world.tick")
        if self.strict and self._ccos is not None and hasattr(self._ccos, "allow"):
            self._ccos.allow(agent_id, *caps)
        else:
            self.bridge.grant(agent_id, *caps)

    def run_thermodynamics_experiment(
        self, agent_id: str = "scientist-1"
    ) -> CivilizationLoopResult:
        self._grant_scientist(agent_id)
        live_before = self.world.hash()
        tick_start = self.world.tick_count

        obs = self.bridge.observe(agent_id, noise=0.02)
        if obs is None:
            return CivilizationLoopResult(
                False, None, None, live_before, live_before, "", notes="observe denied"
            )

        hypothesis = (
            "Heat flows from hot body to cold body until temperatures equalize (Q=mcΔT)."
        )
        prediction = {"final_temps_converge": True, "delta_t_shrinks": True}

        builder = EvidenceBuilder(self.world.name, self.seed)
        builder.record_action({"type": "observe", "agent": agent_id})
        builder.record_action({"type": "hypothesis", "text": hypothesis})

        exp = self.bridge.request_experiment(
            agent_id, ticks=5, interventions=[{"entity_id": 1, "energy": 80.0}]
        )
        if exp is None:
            return CivilizationLoopResult(
                False, None, None, live_before, self.world.hash(), "", notes="experiment denied"
            )

        builder.record_action({"type": "experiment", "id": exp.experiment_id})

        thermo = ThermodynamicsAdapter()
        thermo.add_body(ThermalBody("hot", mass_kg=1.0, temp_k=373.15))
        thermo.add_body(ThermalBody("cold", mass_kg=1.0, temp_k=273.15))
        initial_thermo = thermo.snapshot()
        finals = thermo.step_pair("hot", "cold", steps=200, dt=0.5, k=80.0)
        measurements = [
            {"kind": "thermal_snapshot", "initial": initial_thermo, "final": finals},
            {"kind": "convergence", "delta": abs(finals["hot"] - finals["cold"])},
        ]
        builder.record_action({"type": "thermo_step", "final": finals})

        live_after = self.world.hash()
        if live_after != live_before:
            raise AssertionError(
                f"world experiment mutated live state: before={live_before} after={live_after}"
            )

        pkg = builder.build(
            experiment_id=exp.experiment_id,
            initial_state_hash=live_before,
            final_state_hash=exp.result_hash,
            parent_state_hash=exp.parent_hash,
            tick_start=tick_start,
            tick_end=self.world.tick_count,
            hypothesis=hypothesis,
            prediction=prediction,
            observations=[obs],
            measurements=measurements,
            instruments=["thermo-adapter-v0.1", "lab-fork"],
            uncertainty={"observation_noise": 0.02, "temp_quantization": 1e-6},
        )

        self.provenance.add(
            "experiment",
            live_before,
            exp.result_hash,
            self.world.engine_version,
            self.seed,
            agent_id=agent_id,
            experiment_id=exp.experiment_id,
            evidence_id=pkg.evidence_id,
        )

        oracle = ThermoEquilibriumOracle(tol_k=3.0)
        verdict = oracle.verify({
            "bodies": [
                {"name": "hot", "mass_kg": 1.0, "temp_k": 373.15, "c_j_per_kg_k": 4180.0},
                {"name": "cold", "mass_kg": 1.0, "temp_k": 273.15, "c_j_per_kg_k": 4180.0},
            ],
            "final_temps": finals,
        })
        builder.record_action({
            "type": "oracle",
            "oracle_id": verdict.oracle_id,
            "accepted": verdict.accepted,
            "summary": verdict.summary,
            "details": verdict.details,
        })

        internal_ok = measurements[1]["delta"] < abs(373.15 - 273.15) * 0.8
        supported = internal_ok and verdict.accepted
        discovery = None
        if supported:
            discovery = "thermal_equilibration_confirmed"
            self.knowledge.append(discovery)
            self.ledger.append({
                "type": "discovery",
                "agent": agent_id,
                "discovery": discovery,
                "evidence_id": pkg.evidence_id,
                "evidence_hash": pkg.evidence_hash,
                "oracle_id": verdict.oracle_id,
                "oracle_accepted": True,
            })
        self.ledger.append({
            "type": "evidence",
            "evidence_id": pkg.evidence_id,
            "hash": pkg.evidence_hash,
        })
        self.ledger.append({
            "type": "oracle_verdict",
            "oracle_id": verdict.oracle_id,
            "accepted": verdict.accepted,
            "summary": verdict.summary,
        })

        notes = "ok" if supported else (
            "oracle_rejected" if not verdict.accepted else "prediction not supported"
        )
        return CivilizationLoopResult(
            success=supported and pkg.verify_integrity(),
            evidence=pkg,
            discovery=discovery,
            live_hash_before=live_before,
            live_hash_after=self.world.hash(),
            fork_hash=exp.result_hash,
            ledger_events=list(self.ledger),
            notes=notes,
        )
