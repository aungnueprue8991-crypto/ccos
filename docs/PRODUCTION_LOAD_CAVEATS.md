# Production load caveats (CCOS / NEXUS / AGS)

**Status:** research prototype. Functional tests (including Reality Check Protocol VERIFIED rows) do **not** establish production load readiness.

## Do not claim from green tests alone

| Claim | Why invalid without more evidence |
|-------|-----------------------------------|
| "Handles production traffic" | No SLO, no load generator, no measured p99 |
| "Scales to N agents" | No multi-process/node stress numbers |
| "SQLite is fine at scale" | Connection-per-op; no pool; writer contention untested |
| "Event loop is real-time" | Single-threaded; long discovery loops can block |
| "Memory is durable multi-node" | HybridMemory is in-process; AGS DB is local file |
| "Sandbox is secure under attack" | Often cooperative in-process, not OS isolation |

## Hot spots under load

1. **AGS `AGSDatabase`**: new SQLite connection per transaction/fetch; WAL helps readers, not heavy write fan-out.
2. **NEXUS ecology loop**: sequential handlers; cost grows with event fan-out and max_steps.
3. **Resource leases**: in-process only; no cluster-wide quota authority.
4. **RealityCheck / science loop**: correct and reproducible in lab; not a throughput benchmark.
5. **Bridge AGS\u2192NEXUS**: copies rows into process memory; can amplify RAM if run unbounded.

## Minimum bar for revising this document

- Published load profile (agents, events/s, episode write rate)
- p50/p99 latency and error rate under that profile
- Leak checks for resource leases and DB handles after \u22651h soak
- Failure injection results (process kill, disk full, double release)

Until then, describe the system as **lab-verified**, not production-load-verified.
