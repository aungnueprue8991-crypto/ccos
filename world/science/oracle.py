"""External oracles — independent verification outside the agent's internal loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class OracleVerdict:
    oracle_id: str
    accepted: bool
    score: float
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    independent: bool = True


class ExternalOracle(Protocol):
    oracle_id: str

    def verify(self, claim: Dict[str, Any]) -> OracleVerdict:
        ...


class ThermoEquilibriumOracle:
    oracle_id = "thermo_equilibrium_v1"

    def __init__(self, tol_k: float = 2.0):
        self.tol_k = tol_k

    def verify(self, claim: Dict[str, Any]) -> OracleVerdict:
        bodies: List[Dict[str, Any]] = claim.get("bodies") or []
        finals: Dict[str, float] = claim.get("final_temps") or {}
        if len(bodies) < 2:
            return OracleVerdict(
                self.oracle_id, False, 0.0, "need at least two bodies", {"bodies": len(bodies)}
            )

        num = 0.0
        den = 0.0
        names = []
        for b in bodies:
            m = float(b["mass_kg"])
            c = float(b.get("c_j_per_kg_k", 4180.0))
            t = float(b["temp_k"])
            num += m * c * t
            den += m * c
            names.append(b["name"])
        if den <= 0:
            return OracleVerdict(self.oracle_id, False, 0.0, "invalid heat capacity product")

        t_eq = num / den
        errors = {}
        ok = True
        for name in names:
            if name not in finals:
                ok = False
                errors[name] = None
                continue
            err = abs(float(finals[name]) - t_eq)
            errors[name] = err
            if err > self.tol_k:
                ok = False

        if len(finals) >= 2:
            fvals = [float(finals[n]) for n in names if n in finals]
            if len(fvals) >= 2 and abs(fvals[0] - fvals[1]) > self.tol_k * 2:
                ok = False

        score = 1.0 if ok else max(0.0, 1.0 - max((e or 99) for e in errors.values()) / 50.0)
        return OracleVerdict(
            oracle_id=self.oracle_id,
            accepted=ok,
            score=round(score, 4),
            summary=f"independent T_eq={t_eq:.4f}K; " + ("ACCEPTED" if ok else "REJECTED"),
            details={"t_eq": t_eq, "errors_k": errors, "tol_k": self.tol_k},
            independent=True,
        )


class MassConservationOracle:
    oracle_id = "mass_conservation_v1"

    def verify(self, claim: Dict[str, Any]) -> OracleVerdict:
        initial = claim.get("initial_mass")
        final = claim.get("final_mass")
        tol = float(claim.get("tol", 1e-3))
        if initial is None or final is None:
            return OracleVerdict(self.oracle_id, False, 0.0, "missing initial/final mass")
        ok = abs(float(final) - float(initial)) <= tol
        return OracleVerdict(
            self.oracle_id,
            ok,
            1.0 if ok else 0.0,
            "mass conserved" if ok else "mass not conserved",
            {"initial": initial, "final": final, "tol": tol},
        )


def default_oracles() -> Dict[str, ExternalOracle]:
    return {
        ThermoEquilibriumOracle.oracle_id: ThermoEquilibriumOracle(),
        MassConservationOracle.oracle_id: MassConservationOracle(),
    }
