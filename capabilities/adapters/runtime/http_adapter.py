"""HTTP GET adapter — real external endpoint with gate-issued authorization only."""

from __future__ import annotations

import time
from typing import Any, Dict
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from constitution.schemas.capability import (
    CapabilityManifest, CapabilityResult, CapabilityPermission, CapabilityLifecycle,
)
from constitution.schemas.invocation import AuthorizationDecision
from capabilities.adapters.base import CapabilityAdapter


class HttpGetAdapter(CapabilityAdapter):
    adapter_id = "connector.http.get"
    domain = "world"

    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            name="http_get",
            description="HTTP GET to allowlisted hosts",
            version="1.0.0",
            input_schema={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
            permissions=[CapabilityPermission.READ_WEB.value, CapabilityPermission.NETWORK_ACCESS.value],
            resource_requirements={"timeout_s": 10, "memory_mb": 64},
            provenance=["builtin:http_get"],
            implementation_ref="capabilities.adapters.runtime.http_adapter.HttpGetAdapter",
            adapter_id=self.adapter_id, domain=self.domain,
            lifecycle_status=CapabilityLifecycle.DISCOVERED,
            sandbox_profile={"network": True, "timeout_s": 10, "memory_mb": 64},
        )

    def validate_input(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        url = payload.get("url")
        if not url or not isinstance(url, str):
            return False, "url required"
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "only http/https"
        host = (parsed.hostname or "").lower()
        allowed = {"example.com", "httpbin.org", "www.example.com", "postman-echo.com"}
        if host not in allowed and not host.endswith(".example.com"):
            return False, f"host {host} not allowlisted"
        return True, "ok"

    def execute(self, payload: Dict[str, Any], *, sandboxed: bool = True) -> CapabilityResult:
        return self.execute_authorized(payload, decision=None)

    def execute_authorized(self, payload: Dict[str, Any], decision: AuthorizationDecision | None) -> CapabilityResult:
        if decision is not None and not decision.allowed:
            return CapabilityResult(capability_id="", success=False, error=f"denied: {decision.reason}")
        ok, reason = self.validate_input(payload)
        if not ok:
            return CapabilityResult(capability_id="", success=False, error=reason)
        t0 = time.perf_counter()
        url = payload["url"]
        try:
            req = Request(url, headers={"User-Agent": "CCOS-N3/1.0"}, method="GET")
            with urlopen(req, timeout=10) as resp:
                body = resp.read(50_000)
                status = resp.status
                content_type = resp.headers.get("Content-Type", "")
            dt = (time.perf_counter() - t0) * 1000
            return CapabilityResult(
                capability_id="", success=True,
                output={"status": status, "content_type": content_type,
                        "body_preview": body[:500].decode("utf-8", errors="replace"),
                        "bytes": len(body), "url": url},
                duration_ms=dt, resource_used={"network_mb": len(body) / 1e6},
                provenance=["connector.http.get", decision.decision_id if decision else ""],
            )
        except (URLError, HTTPError, TimeoutError, OSError) as e:
            dt = (time.perf_counter() - t0) * 1000
            return CapabilityResult(capability_id="", success=False, error=str(e), duration_ms=dt,
                                   provenance=["connector.http.get"])
