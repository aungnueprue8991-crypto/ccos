#!/usr/bin/env python3
"""Two-civilization contract demo."""
from pathlib import Path
import tempfile
from agents.civilization.multi import MultiCivilizationCoordinator
from rich.console import Console
console = Console()

def main():
    root = Path(tempfile.mkdtemp(prefix="ccos-civ-"))
    console.rule("[bold]Multi-Civilization Demo[/bold]")
    coord = MultiCivilizationCoordinator(root)
    coord.spawn("Atlantis")
    coord.spawn("Hyperborea")
    c = coord.propose_contract("Atlantis", "Hyperborea", "share verified evidence on climate", ["e-001"])
    coord.accept_contract(c.contract_id, "Hyperborea")
    status = coord.status()
    console.print(status)
    assert all(status["chains_valid"].values())
    assert status["contracts"][c.contract_id]["status"] == "accepted"
    console.rule("[bold green]Multi-civ OK[/bold green]")

if __name__ == "__main__":
    main()
