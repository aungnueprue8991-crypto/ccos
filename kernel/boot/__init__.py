"""COS Boot — production entry."""

from pathlib import Path
from rich.console import Console
from kernel.events.ledger import EventLedger
from constitution.schemas.event import EventEnvelope

console = Console()


def boot(workspace: Path | str = ".") -> EventLedger:
    workspace = Path(workspace)
    console.print("[bold cyan]CCOS COS Boot[/bold cyan]")
    ledger = EventLedger(workspace / "observatory" / "ledger" / "events.db")
    ledger.append(
        EventEnvelope(
            event_type="cos.boot",
            producer_id="cos.kernel",
            payload={"status": "kernel_ready", "workspace": str(workspace.resolve())},
        )
    )
    console.print("[green]Kernel Ready[/green]")
    return ledger


if __name__ == "__main__":
    boot()
