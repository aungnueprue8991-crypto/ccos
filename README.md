# CCOS — Computational Civilization Operating System

**COS executes · COG knows · SCOS discovers · CCOS governs · Hermes orchestrates · Observatory observes**

Production-grade constitutional substrate — all planned phases complete.

## Status v0.3

| Phase | Components | Status |
|-------|------------|--------|
| P0 Foundation | Constitution, schemas, ledger, guards | ✅ |
| P1 COS Kernel | Scheduler, lifecycle, resources, IPC, diagnostics, config | ✅ |
| P2 COG | Evidence, memory, beliefs, knowledge, world model, experience, **reasoning backend** | ✅ |
| P3 SCOS | Hypotheses, experiments, benchmarks, promotion, rollback | ✅ |
| P4 Governance | Decisions, citizens, orgs, policies | ✅ |
| P5 Runtime | Hermes, CLI, tests | ✅ |
| P6 Extended | Population, cosmos, **civilization runtime**, **physics cosmos**, **ledger replication**, **invariant monitor** | ✅ |

## Remaining-phase additions (this pass)

- **Reasoning backend** — Deterministic + optional HTTP LLM; outputs always UNVERIFIED (CCOS-003)
- **Ledger replication** — multi-node append-only sync with chain verification
- **Invariant monitor** — runtime CI checks over the ledger
- **Civilization runtime** — institutions, role teams, task market
- **Physics cosmos** — 2D gravity-lite simulation for SCOS experiments

## Metrics

- ~4300 LOC · 90 modules · **15 tests passing**
- All critical state in SQLite WAL · hash chain verified
- Constitutional guards enforced

## Quick start

```bash
cd ccos && export PYTHONPATH=.
python ccos_cli.py boot
python ccos_cli.py observatory
python -m pytest tests/ -q
```

## Honest boundary

Not claimed: planetary multi-host consensus (Raft/Paxos full), live cloud LLM ops, seL4-style formal proofs, or million-agent economies. Those extend this substrate.
