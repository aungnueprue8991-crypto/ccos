#!/usr/bin/env python3
"""CCOS production CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="ccos", help="Computational Civilization Operating System CLI", no_args_is_help=True)
console = Console()


def _hermes(workspace: str = "."):
    from hermes.shell import Hermes
    return Hermes(workspace)


@app.command()
def boot(workspace: str = typer.Option(".", help="Workspace path")):
    """Boot COS kernel and print status."""
    h = _hermes(workspace)
    s = h.status()
    console.print(f"[green]Booted[/green] events={s['total_events']} chain_valid={s['chain_valid']}")


@app.command()
def intent(
    objective: str = typer.Argument(..., help="Intent objective"),
    issuer: str = typer.Option("human:cli", help="Issuer identity"),
    workspace: str = typer.Option(".", help="Workspace"),
):
    """Submit a root intent."""
    h = _hermes(workspace)
    i = h.submit_intent(issuer=issuer, objective=objective)
    console.print(f"Intent {i.intent_id} committed")


@app.command()
def observatory(workspace: str = typer.Option(".", help="Workspace")):
    """Show Observatory reconstruction summary."""
    h = _hermes(workspace)
    s = h.status()
    table = Table(title="Observatory")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("total_events", str(s["total_events"]))
    table.add_row("db_count", str(s.get("db_count")))
    table.add_row("chain_valid", str(s["chain_valid"]))
    for t, c in sorted(s.get("by_type", {}).items()):
        table.add_row(f"  {t}", str(c))
    console.print(table)


@app.command()
def capabilities(workspace: str = typer.Option(".", help="Workspace")):
    """List registered capabilities."""
    h = _hermes(workspace)
    from constitution.schemas.capability import CapabilityLifecycle
    for status in CapabilityLifecycle:
        caps = h.registry.list_by_status(status)
        if caps:
            console.print(f"[bold]{status.value}[/bold]")
            for c in caps:
                console.print(f"  {c.capability_id[:8]}… {c.name} v{c.version}")


@app.command()
def demo(workspace: str = typer.Option(".", help="Workspace")):
    """Run the production closed-loop demo."""
    from scripts.closed_loop_demo import main as demo_main
    import os
    os.chdir(workspace if workspace != "." else ".")
    demo_main()


if __name__ == "__main__":
    app()
