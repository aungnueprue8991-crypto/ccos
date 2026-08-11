"""Filesystem adapter — read-only under a confined root."""

from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Dict
from constitution.schemas.capability import (
    CapabilityManifest, CapabilityResult, CapabilityPermission, CapabilityLifecycle,
)
from constitution.schemas.invocation import AuthorizationDecision
from capabilities.adapters.base import CapabilityAdapter


class FilesystemAdapter(CapabilityAdapter):
    adapter_id = "connector.fs.read"
    domain = "data"

    def __init__(self, root: str | Path = "/tmp/ccos-fs-sandbox"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        keep = self.root / ".keep"
        if not keep.exists():
            keep.write_text("ccos-fs-sandbox")

    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            name="fs_read", description="Read files under confined sandbox root only", version="1.0.0",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            permissions=[CapabilityPermission.READ_FILE.value],
            resource_requirements={"timeout_s": 2}, provenance=["builtin:fs_read"],
            implementation_ref="capabilities.adapters.runtime.filesystem_adapter.FilesystemAdapter",
            adapter_id=self.adapter_id, domain=self.domain,
            lifecycle_status=CapabilityLifecycle.DISCOVERED,
            sandbox_profile={"filesystem": "readonly_root", "network": False},
        )

    def validate_input(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        rel = payload.get("path")
        if not rel or not isinstance(rel, str):
            return False, "path required"
        if ".." in Path(rel).parts:
            return False, "path escape denied"
        target = (self.root / rel).resolve()
        try:
            target.relative_to(self.root)
        except ValueError:
            return False, "path outside sandbox root"
        return True, "ok"

    def execute(self, payload: Dict[str, Any], *, sandboxed: bool = True) -> CapabilityResult:
        return self.execute_authorized(payload, None)

    def execute_authorized(self, payload: Dict[str, Any], decision: AuthorizationDecision | None) -> CapabilityResult:
        if decision is not None and not decision.allowed:
            return CapabilityResult(capability_id="", success=False, error=f"denied: {decision.reason}")
        ok, reason = self.validate_input(payload)
        if not ok:
            return CapabilityResult(capability_id="", success=False, error=reason)
        target = (self.root / payload["path"]).resolve()
        t0 = time.perf_counter()
        if not target.exists() or not target.is_file():
            return CapabilityResult(capability_id="", success=False, error="file not found")
        data = target.read_bytes()[:20_000]
        dt = (time.perf_counter() - t0) * 1000
        return CapabilityResult(
            capability_id="", success=True,
            output={"path": str(target), "bytes": len(data),
                    "preview": data[:200].decode("utf-8", errors="replace")},
            duration_ms=dt,
            provenance=["connector.fs.read", decision.decision_id if decision else ""],
        )
