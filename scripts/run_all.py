#!/usr/bin/env python3
"""One-command acceptance gate for the ultra plan."""

import subprocess
import sys
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent

def run(cmd):
    print(f"\n>>> {' '.join(cmd)}")
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    return subprocess.call(cmd, cwd=ROOT, env=env)

def main():
    steps = [
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
        [sys.executable, "scripts/closed_loop_demo.py"],
        [sys.executable, "scripts/multi_node_demo.py"],
        [sys.executable, "scripts/multi_civ_demo.py"],
        [sys.executable, "scripts/rsi_demo.py"],
    ]
    for s in steps:
        rc = run(s)
        if rc != 0:
            print(f"FAILED: {s}")
            return rc
    print("\n=== ALL ACCEPTANCE GATES GREEN ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
