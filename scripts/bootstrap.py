#!/usr/bin/env python3
"""One-shot bootstrap: create ledger, register a demo capability, emit events."""

from pathlib import Path
from kernel.boot import boot
from kernel.registry.capability_registry import CapabilityRegistry
from constitution.schemas import CapabilityManifest

def main():
    workspace = Path(".")
    ledger = boot(workspace)
    reg = CapabilityRegistry(ledger)
    demo = CapabilityManifest(
        name="echo",
        description="Simple echo capability for smoke testing",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"echo": {"type": "string"}}},
    )
    reg.register(demo)
    print(f"Registered capability: {demo.capability_id}")
    print(f"Chain valid: {ledger.verify_chain()}")
    print("Bootstrap complete.")

if __name__ == "__main__":
    main()
