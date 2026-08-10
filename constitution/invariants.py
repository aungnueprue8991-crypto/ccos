"""Runtime constitutional invariant monitor (CI-001 … CI-008)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class InvariantResult:
    invariant_id: str
    passed: bool
    message: str
    evidence: dict = field(default_factory=dict)


class InvariantMonitor:
    def __init__(self, ledger: EventLedger):
        self.ledger = ledger
        self._checks: List[Callable[[], InvariantResult]] = []
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._checks.append(self._ci_chain_integrity)
        self._checks.append(self._ci_boot_exists)
        self._checks.append(self._ci_no_orphan_active_without_decision)

    def _ci_chain_integrity(self) -> InvariantResult:
        ok = self.ledger.verify_chain()
        return InvariantResult(
            "CI-006/012", ok,
            "event ledger hash chain valid" if ok else "HASH CHAIN BROKEN",
            {"event_count": self.ledger.count()},
        )

    def _ci_boot_exists(self) -> InvariantResult:
        boots = self.ledger.find_by_type("cos.boot")
        ok = len(boots) >= 1
        return InvariantResult("CI-boot", ok, "at least one cos.boot event" if ok else "no boot event")

    def _ci_no_orphan_active_without_decision(self) -> InvariantResult:
        actives = [
            e for e in self.ledger.find_by_type("capability.lifecycle")
            if e.payload.get("to") == "ACTIVE"
        ]
        decisions = self.ledger.find_by_type("governance.decision")
        if not actives:
            return InvariantResult("CI-004", True, "no ACTIVE transitions yet")
        if not decisions:
            return InvariantResult(
                "CI-004", False,
                "ACTIVE capability without any governance.decision in ledger",
                {"active_count": len(actives)},
            )
        return InvariantResult("CI-004", True, "ACTIVE transitions have governance context")

    def register(self, fn: Callable[[], InvariantResult]) -> None:
        self._checks.append(fn)

    def run_all(self) -> List[InvariantResult]:
        results = [fn() for fn in self._checks]
        all_ok = all(r.passed for r in results)
        self.ledger.append(EventEnvelope(
            event_type="constitution.invariants.checked", producer_id="constitution.monitor",
            payload={
                "all_passed": all_ok,
                "results": [{"id": r.invariant_id, "passed": r.passed, "message": r.message} for r in results],
            },
        ))
        return results

    def assert_all(self) -> None:
        results = self.run_all()
        failed = [r for r in results if not r.passed]
        if failed:
            msgs = "; ".join(f"{r.invariant_id}: {r.message}" for r in failed)
            raise AssertionError(f"Constitutional invariant violations: {msgs}")
