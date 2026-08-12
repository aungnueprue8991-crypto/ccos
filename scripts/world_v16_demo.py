#!/usr/bin/env python3
"""World Engine v1.6 — Reproducible Scientific Civilization Loop demo."""

from world.science.loop import ScientificCivilizationLoop

def main():
    loop = ScientificCivilizationLoop(seed=42)
    result = loop.run_thermodynamics_experiment("scientist-1")
    print("World Engine v1.6 — Scientific Civilization Loop")
    print("=" * 50)
    print(f"success:     {result.success}")
    print(f"discovery:   {result.discovery}")
    print(f"live before: {result.live_hash_before[:16]}…")
    print(f"live after:  {result.live_hash_after[:16]}…")
    print(f"fork hash:   {result.fork_hash[:16]}…")
    if result.evidence:
        print(f"evidence:    {result.evidence.evidence_hash[:16]}…")
        print(f"hypothesis:  {result.evidence.hypothesis[:60]}…")
        print(f"integrity:   {result.evidence.verify_integrity()}")
    print(f"ledger events: {len(result.ledger_events)}")
    print(f"knowledge:   {loop.knowledge}")
    print("OK" if result.success else "FAIL")

if __name__ == "__main__":
    main()
