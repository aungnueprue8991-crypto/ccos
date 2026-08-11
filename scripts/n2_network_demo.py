#!/usr/bin/env python3
"""N2 Network Fabric demo."""
from pathlib import Path
import tempfile
from kernel.network.fabric import NetworkFabric
from constitution.schemas.event import EventEnvelope
from rich.console import Console

console = Console()

def main():
    root = Path(tempfile.mkdtemp(prefix="ccos-n2-"))
    console.rule("[bold]N2 Networked Constitutional Fabric[/bold]")
    fabric = NetworkFabric()
    a = fabric.create_node("alpha", root / "alpha")
    b = fabric.create_node("beta", root / "beta")
    fabric.provision_mesh([a, b])
    a.append_local(EventEnvelope(
        event_type="demo.fact", producer_id=a.identity.node_id,
        payload={"msg": "hello from alpha"},
    ))
    resp = fabric.sync(a.identity.node_id, b.identity.node_id)
    console.print(f"Sync action={resp.action} accepted={resp.accepted} chain={resp.chain_valid}")
    console.print(f"Alpha head={a.head().sequence} Beta head={b.head().sequence}")
    console.print(f"Alpha chain={a.ledger.verify_chain()} Beta chain={b.ledger.verify_chain()}")
    console.rule("[bold green]N2 complete[/bold green]")

if __name__ == "__main__":
    main()
