#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NEXUS_HOME="${NEXUS_HOME:-$HOME/.nexus}"
BIN_DIR="${NEXUS_BIN_DIR:-$HOME/.local/bin}"
echo "==> NEXUS x CCOS install"
mkdir -p "$NEXUS_HOME"/{data/workflows,logs,agents,skills} "$BIN_DIR"
cat > "$BIN_DIR/nexus" << SH
#!/usr/bin/env bash
export NEXUS_HOME="\${NEXUS_HOME:-$NEXUS_HOME}"
export NEXUS_DATA="\${NEXUS_DATA:-\$NEXUS_HOME/data}"
export PYTHONPATH="$ROOT\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 "$ROOT/scripts/nexus" "\$@"
SH
chmod +x "$BIN_DIR/nexus" "$ROOT/scripts/nexus" "$ROOT/scripts/install.sh" "$ROOT/scripts/setup_and_run.sh" 2>/dev/null || true
echo "==> Installed CLI: $BIN_DIR/nexus"
echo "    Run: nexus setup --quick && nexus doctor"
