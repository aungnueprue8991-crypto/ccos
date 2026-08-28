# CCOS — Computational Civilization Operating System

**COS executes · COG knows · SCOS discovers · CCOS governs · Hermes orchestrates · AGS develops · World Engine provides reality**

Production-grade constitutional substrate for governed multi-agent scientific civilizations.

## Architecture

```
HUMAN / WORLD
     │
     ▼
┌─────────────────────────────────────┐
│              CCOS                    │
│  Constitution · Governance · Ledger  │
└──────────────────┬──────────────────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
   AGS          WORLD         HERMES
 (organisms)   (reality)   (orchestrator)
     │             │
     └──────┬──────┘
            ▼
     Evidence Packages
            ▼
     Knowledge / Discovery
```

## Status (v1.6+)

| Layer | Components | Status |
|-------|------------|--------|
| CCOS Kernel | Constitution, ledger, capabilities, governance | ✅ |
| AGS v1.0–v1.5 | Genome, memory, collaboration, reproduction | ✅ |
| World Engine | Deterministic ECS, forks, evidence packages | ✅ |
| NEXUS | Cognitive ecology, Thought→Reasoning→Evidence | ✅ |
| RealityCheck | 15-rule protocol, epistemic authority | ✅ |

## Hard invariants

- Unknown capability → **DENY**
- Observation ≠ ground truth
- Experiments run on **forks**, never live world
- Reproduction is a **transaction** (not auto-spawn)
- Memory ≠ belief; knowledge requires verification
- Same seed + actions → same state hash

## Quick start

```bash
cd ccos
pip install -r requirements.txt
export PYTHONPATH=.

# World Engine demo
python scripts/world_engine_demo.py

# Tests
python -m pytest tests/ags/ tests/world/ tests/nexus/ -q
```

## License

Project code — see repository terms.
