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

## Status (v1.6)

| Layer | Components | Status |
|-------|------------|--------|
| CCOS Kernel | Constitution, ledger, capabilities, governance | ✅ |
| AGS v1.0 | Genome, memory, curiosity, modular agent | ✅ |
| AGS v1.1 | Collective observation, 3-agent discovery | ✅ |
| AGS v1.2 | Teaching + provenance (UNVERIFIED→VERIFIED) | ✅ |
| AGS v1.3 | Collaboration teams, roles, evidence pool | ✅ |
| AGS v1.4 | Research programs, hypothesis competition | ✅ |
| AGS v1.5 | Controlled reproduction (CCOS-gated) | ✅ |
| World Engine | Deterministic ECS, hash, snapshot, replay | ✅ |
| World v1.6 | Scientific civilization loop, evidence packages | ✅ |
| Adapters | Thermo, chemistry, biology, ecology, climate | ✅ |

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
python scripts/world_v16_demo.py

# Tests
python -m pytest tests/ags/ tests/world/ -q
```

## Repository layout

```
ccos/
├── constitution/     # CCOS constitutional layer
├── kernel/           # COS runtime kernel
├── ags/              # Agent Genesis System
│   ├── genome/ memory/ evolution/ collaboration/
│   ├── v11/ v12/ v14/ living/ reference/
├── world/            # World Engine
│   ├── core/ state/ laboratory/ observation/
│   ├── adapters/ evidence/ science/ governance/
├── hermes/           # Orchestrator
├── tests/
└── scripts/
```

## License

Project code — see repository terms.
