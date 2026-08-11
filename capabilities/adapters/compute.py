"""Safe compute adapter — arithmetic only."""

from __future__ import annotations
import operator
import time
from typing import Any, Dict
from constitution.schemas.capability import (
    CapabilityManifest, CapabilityResult, CapabilityPermission, CapabilityLifecycle,
)
from capabilities.adapters.base import CapabilityAdapter

OPS = {
    "add": operator.add, "sub": operator.sub, "mul": operator.mul,
    "div": lambda a, b: a / b if b != 0 else float("nan"),
}


class ComputeAdapter(CapabilityAdapter):
    adapter_id = "connector.compute"
    domain = "compute"

    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            name="safe_compute", description="Whitelist arithmetic", version="1.0.0",
            input_schema={"type": "object", "properties": {
                "op": {"type": "string", "enum": list(OPS.keys())},
                "a": {"type": "number"}, "b": {"type": "number"},
            }, "required": ["op", "a", "b"]},
            permissions=[CapabilityPermission.COMPUTE.value],
            resource_requirements={"cpu": 0.1, "memory_mb": 16, "timeout_s": 2},
            provenance=["builtin:compute"],
            implementation_ref="capabilities.adapters.compute.ComputeAdapter",
            adapter_id=self.adapter_id, domain=self.domain,
            lifecycle_status=CapabilityLifecycle.DISCOVERED,
            sandbox_profile={"network": False, "filesystem": "none", "timeout_s": 2, "memory_mb": 32},
        )

    def validate_input(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        if payload.get("op") not in OPS:
            return False, f"op must be one of {list(OPS)}"
        try:
            float(payload["a"]); float(payload["b"])
        except (KeyError, TypeError, ValueError):
            return False, "a and b must be numbers"
        return True, "ok"

    def execute(self, payload: Dict[str, Any], *, sandboxed: bool = True) -> CapabilityResult:
        ok, reason = self.validate_input(payload)
        if not ok:
            return CapabilityResult(capability_id="", success=False, error=reason)
        t0 = time.perf_counter()
        result = OPS[payload["op"]](float(payload["a"]), float(payload["b"]))
        dt = (time.perf_counter() - t0) * 1000
        return CapabilityResult(
            capability_id="", success=True,
            output={"result": result, "op": payload["op"]}, duration_ms=dt,
            resource_used={"cpu": 0.01, "memory_mb": 0.5}, provenance=["connector.compute"],
        )
