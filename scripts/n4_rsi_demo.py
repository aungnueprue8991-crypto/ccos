#!/usr/bin/env python3
"""N4 Real RSI Evaluation Plane demo."""
from pathlib import Path
import tempfile
from hermes.shell import Hermes
from rich.console import Console
from rich.table import Table
console = Console()

def eval_good(impl):
    boost = float(impl.get("boost", 0.1))
    return {"success_rate": 0.80 + boost, "latency_norm": max(0.05, 0.30 - boost * 0.5),
            "accuracy": 0.80 + boost, "safety": 1.0}

def eval_bad(impl):
    return {"success_rate": 0.55, "latency_norm": 0.8, "accuracy": 0.55, "safety": 0.6}

def main():
    ws = Path(tempfile.mkdtemp(prefix="ccos-n4-"))
    console.rule("[bold]N4 RSI Evaluation Plane[/bold]")
    h = Hermes(ws)
    table = Table(title="RSI Cycles")
    for col in ["Case", "Status", "Verified", "Activated", "Gain"]:
        table.add_column(col)
    out1 = h.n4.run_full_cycle("planner", "strategy Y", {"boost": 0.14, "strategy": "Y"}, eval_good)
    table.add_row("good", out1["status"], str(out1["verified"]), str(out1["activated"]),
                  f"{out1['score'].get('capability_gain', 0):.3f}")
    out2 = h.n4.run_full_cycle("planner", "weak", {"boost": -0.2}, eval_bad)
    table.add_row("weak", out2["status"], str(out2["verified"]), str(out2["activated"]),
                  f"{out2['score'].get('capability_gain', 0):.3f}")
    h.n4.rollback(out1["experiment_id"], "citizen:governor", reason="canary anomaly")
    table.add_row("rollback", "ROLLED_BACK", "-", "False", "-")
    console.print(table)
    h.n4.assert_no_direct_mutation()
    console.print(f"Chain: {h.ledger.verify_chain()} Archive: {h.archive.count()}")
    console.rule("[bold green]N4 complete[/bold green]")

if __name__ == "__main__":
    main()
