#!/usr/bin/env python3
"""Governed RSI demo — N cycles, zero auto-activation, full audit."""
from pathlib import Path
import tempfile
from hermes.shell import Hermes
from evolution.archive.store import ExperimentArchive
from evolution.benchmarks.split import SplitBenchmarkHarness, SplitScore
from evolution.rsi.loop import GovernedRSILoop, RSICandidate, CandidateKind, PromotionPredicate
from rich.console import Console
from rich.table import Table
console = Console()

def main():
    ws = Path(tempfile.mkdtemp(prefix="ccos-rsi-"))
    console.rule("[bold]Governed RSI Demo[/bold]")
    h = Hermes(ws)
    archive = ExperimentArchive(h.ledger, ws / "archive.db")
    split = SplitBenchmarkHarness(h.ledger)
    loop = GovernedRSILoop(
        h.ledger, h.hypotheses, h.experiments, archive, split, h.governance, h.registry,
        predicate=PromotionPredicate(min_public=0.55, min_private=0.55, min_safety=0.8),
    )
    def evaluate(params):
        decay = float(params.get("energy_decay", 0.05))
        accuracy = max(0.0, min(1.0, 1.0 - decay * 5))
        heldout = max(0.0, min(1.0, accuracy - 0.05 + (0.02 if decay < 0.03 else -0.02)))
        return SplitScore(public={"accuracy": accuracy, "efficiency": 1.0 - decay}, private={"heldout": heldout, "safety": 0.95})
    def factory(cycle):
        return RSICandidate(kind=CandidateKind.COSMOS_PARAM, description=f"reduce energy_decay cycle {cycle}",
                            payload={"energy_decay": max(0.005, 0.08 - cycle * 0.01)}, rollback_target="cosmos-baseline-v0")
    results = loop.run_n(8, "improve cosmos energy efficiency", evaluate, factory, auto_governance=True)
    loop.assert_no_auto_activation()
    table = Table(title="RSI Cycles")
    for col in ["Cycle", "Public", "Private", "Gates", "Decision", "Activated"]:
        table.add_column(col)
    for r in results:
        table.add_row(str(r.cycle), f"{r.public_score:.3f}", f"{r.private_score:.3f}",
                      "PASS" if r.gates_passed else "FAIL", r.decision or "-", str(r.activated))
    console.print(table)
    console.print(f"Archive runs: {archive.count()} | Chain: {h.ledger.verify_chain()} | Events: {h.ledger.count()}")
    console.rule("[bold green]RSI complete — zero auto-activations[/bold green]")

if __name__ == "__main__":
    main()
