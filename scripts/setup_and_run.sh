#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export NEXUS_HOME="${NEXUS_HOME:-$HOME/.nexus}"
export NEXUS_DATA="${NEXUS_DATA:-$NEXUS_HOME/data}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
echo "NEXUS x CCOS setup and run"
bash "$ROOT/scripts/install.sh"
mkdir -p "$NEXUS_HOME" "$NEXUS_DATA/workflows"
ARGS=(setup --quick)
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  ARGS=(setup --full --provider openai --api-key "$OPENAI_API_KEY")
elif [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  ARGS=(setup --full --provider anthropic --api-key "$ANTHROPIC_API_KEY")
fi
python3 "$ROOT/scripts/nexus" "${ARGS[@]}"
python3 "$ROOT/scripts/nexus" doctor
python3 "$ROOT/scripts/nexus" start --once
echo READY
