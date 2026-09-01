# NEXUS x CCOS Setup Plan (Hermes/OpenClaw style)

## Quick start
```bash
./scripts/setup_and_run.sh
# or
./scripts/install.sh && nexus setup --quick && nexus doctor && nexus start --once
```

## API keys
```bash
nexus setup --full --provider openai --api-key "$OPENAI_API_KEY"
nexus model --provider anthropic --api-key "$ANTHROPIC_API_KEY"
```

## Gaps via env
- DATABASE_URL for Postgres
- TEMPORAL_HOST + WORKFLOW_BACKEND=temporal

See deploy/README.md and RESIDUAL_GAPS.md.
