#!/usr/bin/env python3
"""Run the *reference* agent (different code from modular AGSAgent)."""
from ags.reference.runtime import run_demo

if __name__ == "__main__":
    run_demo(cycles=6)
