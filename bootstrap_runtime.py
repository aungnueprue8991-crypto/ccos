#!/usr/bin/env python3
"""Bootstrap NEXUS x CCOS runtime and print status."""
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("NEXUS_DATA", str(ROOT / "data"))

def main() -> int:
    from ccos.runtime_factory import create_runtime
    rt = create_runtime(os.environ["NEXUS_DATA"])
    status = rt.supervisor.status()
    print("bootstrap: ready", status.get("safety", {}))
    print("gateway", rt.gateway.coverage())
    print("persist", rt.store.counts() if hasattr(rt, "store") else {})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
