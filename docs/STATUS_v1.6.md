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

## Verification (single command)

```bash
bash scripts/smoke.sh
# Requires: PYTHONPATH=., pytest, hypothesis
# Covers: determinism, science loop demo, materials, world + AGS core tests
```

Focused suites that have been green after P0 fixes:
- `tests/world/` (including materials elastic/plastic split)
- `tests/ags/test_v12_teaching.py` … `test_v15_reproduction.py`
- `tests/world/integration/test_v16_loop.py` (Hypothesis)

Do **not** claim a fixed “116 tests green” without a clean CI run on a pinned environment.

## Invariants held (in code paths exercised)

- DENY unknown capabilities
- Fork isolation (live hash unchanged)
- Same seed → same hash
- Reproduction is transactional (in-process)
- Evidence packages hash-integrity verified

## What is *not* claimed

- Production-grade multi-node deployment
- OS-level sandbox isolation
- Real LLM-driven open-ended discovery by default (MockAdapter in many paths)
- Continuum / high-fidelity scientific simulators
- Formal verification of the constitution
- Sustained production load, SLO latency, or multi-tenant isolation under traffic

## Production load caveats

This codebase is a **lab / research prototype**. Green unit tests and protocol VERIFIED probes measure **functional correctness**, not production capacity.

### Concurrency and process model

| Area | Current behavior | Load implication |
|------|------------------|------------------|
| AGS SQLite | New connection per `tx`/`fetch`; WAL on | Fine for single-agent lab; weak under many concurrent writers |
| Thread-local `get_db()` | One DB handle per thread default path | Not a connection pool; no max-connection policy |
| NEXUS HybridMemory | In-process structures | Not shared across processes; no horizontal scale |
| Ecology event loop | Single-threaded handlers | Long discovery steps can block |

### Memory and durability

- HybridMemory compress/decay is in-process — not proven at large N.
- FTS5 is best-effort; without FTS, search falls back to `LIKE`.
- EventLedger is local-file oriented — not a replicated log.

### Cognitive / discovery path

- RealityCheck and ecology probes are correctness tests, not latency/throughput benchmarks.
- Serendipity / dream / evolution checks validate behavior, not CPU-hour budgets under continuous idle research.
- Model router uses seeded profiles — not live multi-LLM rate limits, cost caps, or tail latency.

### Security and isolation under load

- Many adapters use cooperative in-process sandbox — **not** OS container isolation under attack load.
- Federation crypto is prototype-grade; not capacity-tested as a multi-civilization mesh.
- Governance policy injection is optional on some paths — do not assume every hot path is policy-gated under stress.

### Required before any “production load” claim

1. Defined SLOs (p50/p99, error budget) and a load generator.
2. Connection pooling + bounded queues for DB and event loops.
3. Multi-process/node stress with non-leaking resource leases.
4. Durable ledger/memory backends with backup/restore drills.
5. Chaos tests (kill mid-experiment, double-release, disk full) with measured recovery.
6. Capacity numbers tied to hardware — never inferred from pytest pass counts.

Until those exist, all performance language is **lab-scale observation only**.

## Next (path from demo → reality)

See research synthesis in project discussion / ULTRA_PLAN updates:
- P0: smoke + honest status (this doc) + materials/API test fixes
- P1: unify agent lineage; single CCOS client path for all gated actions
- P2: property tests under load; durable multi-tick civilization demo
- P3: process/container sandbox; multi-process federation
- External coupling: lab-in-the-loop or verified benchmarks (Robin, AISAC, EinsteinArena patterns)

## CCOS-NEXUS (cognitive layer)

New package `nexus/` implements the emergent cognition blueprint on CCOS substrate:

- drives + arbitration
- question engine + evaluator
- idea operators + MAD arena
- imagination, causality, abstraction, transfer
- invention (draft artifacts only)
- metacognition (Q-vector), consolidation, curriculum
- emergence checklist (strict)
- `CognitiveOrchestrator` wiring Loop B to world science + oracle

```bash
PYTHONPATH=. python scripts/nexus_demo.py
PYTHONPATH=. python -m pytest tests/nexus/ -q
```

NEXUS does not bypass CCOS gates; world experiments still go through capability bridge + oracle.
