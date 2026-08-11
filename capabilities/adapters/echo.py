"""Echo adapter — first real connector proving full lifecycle."""

from __future__ import annotations
import time
from typing import Any, Dict
from constitution.schemas.capability import (
    CapabilityManifest, CapabilityResult, CapabilityPermission, CapabilityLifecycle,
)
from capabilities.adapters.base import CapabilityAdapter


class EchoAdapter(CapabilityAdapter):
    adapter_id = "connector.echo"
    domain = "compute"

    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            name="echo", description="Deterministic echo capability", version="1.0.0",
            input_schema={"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
            output_schema={"type": "object", "properties": {"echo": {"type": "string"}}},
            permissions=[CapabilityPermission.COMPUTE.value, CapabilityPermission.READ_ONLY.value],
            resource_requirements={"cpu": 0.1, "memory_mb": 32, "timeout_s": 5},
            provenance=["builtin:echo"],
            implementation_ref="capabilities.adapters.echo.EchoAdapter",
            adapter_id=self.adapter_id, domain=self.domain,
            lifecycle_status=CapabilityLifecycle.DISCOVERED,
            sandbox_profile={"network": False, "filesystem": "none", "timeout_s": 5, "memory_mb": 64},
        )

    def validate_input(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        if not isinstance(payload, dict):
            return False, "payload must be dict"
        if "message" not in payload:
            return False, "message required"
        if not isinstance(payload["message"], str):
            return False, "message must be str"
        if len(payload["message"]) > 10_000:
            return False, "message too long"
        return True, "ok"

    def execute(self, payload: Dict[str, Any], *, sandboxed: bool = True) -> CapabilityResult:
        ok, reason = self.validate_input(payload)
        if not ok:
            return CapabilityResult(capability_id="", success=False, error=reason)
        t0 = time.perf_counter()
        msg = payload["message"]
        out = {"echo": msg, "length": len(msg), "sandboxed": sandboxed}
        dt = (time.perf_counter() - t0) * 1000
        return CapabilityResult(
            capability_id="", success=True, output=out, duration_ms=dt,
            resource_used={"cpu": 0.01, "memory_mb": 1.0}, provenance=["connector.echo"],
        )
