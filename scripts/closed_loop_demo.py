#!/usr/bin/env python3
"""Production closed-loop demonstration of the CCOS intelligence metabolism."""

from constitution.schemas import (
    CapabilityManifest,
    CapabilityLifecycle,
    Experiment,
    MemoryRecord,
    MemoryKind,
)
from hermes.shell import Hermes
from rich.console import Console
from rich.table import Table

console = Console()


def main():
    console.rule("[bold]CCOS Production Closed-Loop Demo[/bold]")
    h = Hermes(workspace=".")

    intent = h.submit_intent(
        issuer="human:architect",
        objective="Discover and safely promote a better echo capability",
        constraints=["must pass independent verification", "no auto-activation"],
    )
    console.print(f"[cyan]Intent[/cyan]: {intent.intent_id}")

    ev = h.evidence.ingest_observation(
        claim="Current echo capability has latency > 50ms under load",
        source="synthetic_benchmark",
        observation_refs=["bench-001"],
    )
    ev = h.evidence.validate(ev.evidence_id, confidence=0.85, methodology="synthetic load test")
    ev = h.evidence.corroborate(ev.evidence_id, ["bench-002", "bench-003"])
    console.print(f"[cyan]Evidence[/cyan]: {ev.epistemic_status.value} conf={ev.confidence}")

    rec = MemoryRecord(
        namespace="scientific",
        kind=MemoryKind.SCIENTIFIC,
        content={"claim": ev.claim, "evidence_id": ev.evidence_id},
        provenance=[ev.evidence_id],
        epistemic_status=ev.epistemic_status,
        writer="cog.pipeline",
    )
    h.memory.write(rec)
    console.print("[cyan]Memory write[/cyan] accepted")

    manifest = CapabilityManifest(
        name="echo-v2",
        description="Lower-latency echo",
        version="0.2.0",
        provenance=[ev.evidence_id],
    )
    experiment = Experiment(
        hypothesis_ref="h-latency",
        parameters={"target_latency_ms": 20},
        metrics={"p99_latency_ms": 18.4, "accuracy": 1.0},
        random_seed=42,
        provenance=[ev.evidence_id],
        reproducible=True,
    )
    candidate = h.promotion.propose_candidate(
        manifest, experiment, benchmarks={"latency": 18.4, "safety": 1.0}
    )
    console.print(f"[cyan]Candidate[/cyan]: {candidate.candidate_id}")

    prop = h.promotion.request_governance_approval(candidate.candidate_id, proposer="scos")
    decision = h.governance.decide(
        prop.proposal_id,
        decision_maker="citizen:governance-officer",
        outcome="APPROVED",
        rationale="Benchmarks pass, evidence CORROBORATED",
    )
    console.print(f"[green]Decision[/green]: {decision.outcome}")

    h.registry.transition(
        manifest.capability_id,
        CapabilityLifecycle.APPROVED,
        reason="governance approved",
        authorized_by=decision.decision_maker,
    )
    h.registry.transition(
        manifest.capability_id,
        CapabilityLifecycle.ACTIVE,
        reason="promote to production",
        authorized_by=decision.decision_maker,
    )
    console.print("[green]Capability ACTIVE[/green]")

    summary = h.status()
    table = Table(title="Observatory Reconstruction")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Total events", str(summary["total_events"]))
    table.add_row("DB count", str(summary["db_count"]))
    table.add_row("Chain valid", str(summary["chain_valid"]))
    for t, c in sorted(summary["by_type"].items()):
        table.add_row(f"  {t}", str(c))
    console.print(table)
    console.rule("[bold green]Closed loop completed — constitutional constraints enforced[/bold green]")


if __name__ == "__main__":
    main()
