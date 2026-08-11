"""Process adapter — whitelist of safe subprocess commands only."""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict

from constitution.schemas.capability import (
    CapabilityManifest, CapabilityResult, CapabilityPermission, CapabilityLifecycle,
)
from constitution.schemas.invocation import AuthorizationDecision
from capabilities.adapters.base import CapabilityAdapter

ALLOWED_CMDS = {"echo": ["echo"], "date": ["date", "-u"], "uname": ["uname", "-a"]}


class ProcessAdapter(CapabilityAdapter):
    adapter_id = "connector.process.safe"
    domain = "compute"

    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            name="safe_process",
            description="Whitelist subprocess (echo/date/uname only)",
            version="1.0.0",
            input_schema={"type": "object", "properties": {
                "cmd": {"type": "string", "enum": list(ALLOWED_CMDS.keys())},
                "args": {"type": "array", "items": {"type": "string"}},
            }, "required": ["cmd"]},
            permissions=[CapabilityPermission.EXECUTE_CODE.value],
            resource_requirements={"timeout_s": 5, "memory_mb": 32},
            provenance=["builtin:process"],
            implementation_ref="capabilities.adapters.runtime.process_adapter.ProcessAdapter",
            adapter_id=self.adapter_id, domain=self.domain,
            lifecycle_status=CapabilityLifecycle.DISCOVERED,
            sandbox_profile={"network": False, "timeout_s": 5},
        )

    def validate_input(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        cmd = payload.get("cmd")
        if cmd not in ALLOWED_CMDS:
            return False, f"cmd must be one of {list(ALLOWED_CMDS)}"
        args = payload.get("args") or []
        if not isinstance(args, list) or any(not isinstance(a, str) for a in args):
            return False, "args must be list[str]"
        if len(args) > 8:
            return False, "too many args"
        return True, "ok"

    def execute(self, payload: Dict[str, Any], *, sandboxed: bool = True) -> CapabilityResult:
        return self.execute_authorized(payload, None)

    def execute_authorized(self, payload: Dict[str, Any], decision: AuthorizationDecision | None) -> CapabilityResult:
        if decision is not None and not decision.allowed:
            return CapabilityResult(capability_id="", success=False, error=f"denied: {decision.reason}")
        ok, reason = self.validate_input(payload)
        if not ok:
            return CapabilityResult(capability_id="", success=False, error=reason)
        base = list(ALLOWED_CMDS[payload["cmd"]])
        args = payload.get("args") or []
        cmd = base + (args if payload["cmd"] == "echo" else [])
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
            dt = (time.perf_counter() - t0) * 1000
            return CapabilityResult(
                capability_id="", success=proc.returncode == 0,
                output={"stdout": proc.stdout[:2000], "stderr": proc.stderr[:500], "returncode": proc.returncode},
                error=None if proc.returncode == 0 else f"exit {proc.returncode}", duration_ms=dt,
                provenance=["connector.process.safe", decision.decision_id if decision else ""],
            )
        except Exception as e:
            return CapabilityResult(capability_id="", success=False, error=str(e))
