#!/usr/bin/env python3
"""N5 Multi-Civilization Federation demo."""
from pathlib import Path
import tempfile
from federation.plane import FederationPlane
from rich.console import Console
from rich.table import Table
console = Console()

def main():
    root = Path(tempfile.mkdtemp(prefix="ccos-n5-"))
    console.rule("[bold]N5 Multi-Civilization Federation[/bold]")
    plane = FederationPlane()
    a = plane.spawn("Atlantis", root / "atlantis")
    b = plane.spawn("Hyperborea", root / "hyperborea")
    c = plane.spawn("Lemuria", root / "lemuria")
    for x, y in [(a, b), (a, c), (b, c)]:
        plane.discover(x.identity.civilization_id, y.identity.civilization_id)
        plane.attest(x.identity.civilization_id, y.identity.civilization_id)
    plane.negotiate_treaty(a.identity.civilization_id, b.identity.civilization_id, scope="research")
    plane.negotiate_treaty(b.identity.civilization_id, c.identity.civilization_id, scope="science")
    plane.share_knowledge(a.identity.civilization_id, b.identity.civilization_id,
                          claims=["ocean salinity rising"], evidence_refs=["obs-42"])
    plane.share_capability(a.identity.civilization_id, b.identity.civilization_id,
                           "tidal-model-v1", {"name": "tidal-model-v1"})
    def ev(impl):
        return {"success_rate": 0.91, "latency_norm": 0.18, "accuracy": 0.91, "safety": 1.0}
    syn = plane.joint_experiment(a.identity.civilization_id,
                                 [b.identity.civilization_id, c.identity.civilization_id],
                                 "multi-civ boost", ev, {"boost": 0.13})
    plane.revoke(c.identity.civilization_id, a.identity.civilization_id, reason="forged evidence")
    plane.assert_sovereignty()
    table = Table(title="Federation Status")
    for col in ["Civilization", "Treaties", "Evidence", "Caps", "Chain"]:
        table.add_column(col)
    for s in plane.status():
        table.add_row(s["name"], str(s["treaties"]), str(s["evidence_inbox"]),
                      str(s["capability_offers"]), str(s["chain_valid"]))
    console.print(table)
    console.print(f"Joint all_verified={syn['all_verified']}")
    console.rule("[bold green]N5 complete — sovereignty preserved[/bold green]")

if __name__ == "__main__":
    main()
