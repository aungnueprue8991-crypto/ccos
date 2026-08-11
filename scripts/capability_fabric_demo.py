#!/usr/bin/env python3
"""N1 Capability Fabric demo."""
from pathlib import Path
import tempfile
from hermes.shell import Hermes
from capabilities.adapters.echo import EchoAdapter
from capabilities.adapters.compute import ComputeAdapter
from rich.console import Console

console = Console()

def main():
    ws = Path(tempfile.mkdtemp(prefix="ccos-n1-"))
    console.rule("[bold]N1 Governed Capability Fabric[/bold]")
    h = Hermes(ws)
    for adapter, payload in [
        (EchoAdapter(), {"message": "hello-fabric"}),
        (ComputeAdapter(), {"op": "add", "a": 2, "b": 3}),
    ]:
        out = h.fabric.full_lifecycle(adapter, execute_payload=payload)
        console.print(f"{adapter.adapter_id}: activated={out.activated} public={out.public_score:.3f}")
    console.print(f"Chain valid: {h.ledger.verify_chain()}")
    console.rule("[bold green]N1 complete[/bold green]")

if __name__ == "__main__":
    main()
