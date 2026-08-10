#!/usr/bin/env python3
"""Multi-node ledger replication demo."""
from pathlib import Path
import tempfile
from constitution.schemas.event import EventEnvelope
from kernel.events.replication import ReplicationCluster
from rich.console import Console
console = Console()

def main():
    root = Path(tempfile.mkdtemp(prefix="ccos-nodes-"))
    console.rule("[bold]Multi-Node Replication[/bold]")
    cluster = ReplicationCluster()
    a = cluster.add_node("alpha", root / "alpha")
    b = cluster.add_node("beta", root / "beta")
    for i in range(5):
        a.append_local(EventEnvelope(event_type="demo.ping", producer_id="alpha", payload={"i": i}))
    result = cluster.sync(a.node_id, b.node_id)
    console.print(result)
    assert result["imported"] == 5 and result["target_chain_valid"] is True
    b.append_local(EventEnvelope(event_type="demo.pong", producer_id="beta", payload={"ok": True}))
    console.print(cluster.sync(b.node_id, a.node_id))
    console.print(cluster.status())
    console.rule("[bold green]Sync OK[/bold green]")

if __name__ == "__main__":
    main()
