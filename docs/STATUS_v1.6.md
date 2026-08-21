# CCOS Project Status — v1.6 (research prototype)

Honest status: **working research architecture**, not a production OS or civilization-scale system.

## What is implemented and verified

1. CCOS constitutional patterns (ledger, capabilities, governance gates)
2. AGS developmental agents (genome → memory → curiosity; multiple lineages)
3. Collective / teaching / collaboration / science program modules (v1.1–v1.4)
4. Controlled reproduction (v1.5) — gated, fitness-vector, lineage ledger
5. World Engine deterministic ECS + forks + observation ≠ ground truth
6. World v1.6 scientific civilization loop + evidence packages
7. Numeric adapters (thermo, chemistry, biology, ecology, climate, physics, materials)
8. **Strict-mode capability bridge** (`CCOS_STRICT=1` / `strict=True`) — local grants ignored
9. **External oracles** — independent thermo equilibrium + mass conservation checks

## Verification (single command)

```bash
bash scripts/smoke.sh
# Requires: PYTHONPATH=., pytest, hypothesis
```

## Invariants held (in code paths exercised)

- DENY unknown capabilities
- Strict mode: local grants never bypass CCOS client
- Fork isolation (live hash unchanged)
- Same seed → same hash
- Reproduction is transactional (in-process)
- Evidence packages hash-integrity verified
- Discovery requires **external oracle accept**, not only internal support

## What is *not* claimed

- Production-grade multi-node deployment
- OS-level sandbox isolation
- Real LLM-driven open-ended discovery by default (MockAdapter in many paths)
- Continuum / high-fidelity scientific simulators
- Formal verification of the constitution

## Next (path from demo → reality)

- P1: unify agent lineage; single CCOS client path for all gated actions
- P2: property tests under load; durable multi-tick civilization demo
- P3: process/container sandbox; multi-process federation
- External coupling: lab-in-the-loop or verified benchmarks (Robin / AISAC patterns)
