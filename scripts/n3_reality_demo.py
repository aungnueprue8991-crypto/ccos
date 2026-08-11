#!/usr/bin/env python3
"""N3 Reality Plane demo."""
from pathlib import Path
import tempfile
from hermes.shell import Hermes
from constitution.schemas.invocation import InvocationEnvelope
from capabilities.adapters.echo import EchoAdapter
from capabilities.adapters.runtime.process_adapter import ProcessAdapter
from capabilities.adapters.runtime.filesystem_adapter import FilesystemAdapter
from rich.console import Console
from rich.table import Table
console = Console()

def promote(h, adapter, payload):
    return h.fabric.full_lifecycle(adapter, execute_payload=payload)

def main():
    ws = Path(tempfile.mkdtemp(prefix="ccos-n3-"))
    console.rule("[bold]N3 Reality Plane[/bold]")
    h = Hermes(ws)
    table = Table(title="Invocation Results")
    for col in ["Case", "Allowed", "Success", "Detail"]:
        table.add_column(col)
    o = promote(h, EchoAdapter(), {"message": "ok"})
    inv = InvocationEnvelope(capability_id=o.capability_id, issuer="agent:a", intent_id="i1",
                             input_payload={"message": "hello-reality"})
    d, r = h.invoker.invoke(inv, EchoAdapter())
    table.add_row("echo success", str(d.allowed), str(r.success), str(r.output)[:50])
    m = h.fabric.register_adapter(EchoAdapter())
    inv2 = InvocationEnvelope(capability_id=m.capability_id, issuer="agent:a", input_payload={"message": "x"})
    d2, r2 = h.invoker.invoke(inv2, EchoAdapter())
    table.add_row("deny inactive", str(d2.allowed), str(r2.success), d2.reason[:40])
    po = promote(h, ProcessAdapter(), {"cmd": "echo", "args": ["n3"]})
    inv3 = InvocationEnvelope(capability_id=po.capability_id, issuer="agent:ops", intent_id="i-proc",
                              input_payload={"cmd": "echo", "args": ["governed"]})
    d3, r3 = h.invoker.invoke(inv3, ProcessAdapter())
    table.add_row("process", str(d3.allowed), str(r3.success), (r3.output or {}).get("stdout", "")[:30])
    console.print(table)
    console.print(f"Chain: {h.ledger.verify_chain()}")
    console.rule("[bold green]N3 complete[/bold green]")

if __name__ == "__main__":
    main()
