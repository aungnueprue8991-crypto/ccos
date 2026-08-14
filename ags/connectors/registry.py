"""Phase 10 — external connectors registry; all calls require CCOS capability."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ags.ccos_kernel.kernel import CivilizationCCOS, Decision


class ConnectorRegistry:
    def __init__(self, ccos: CivilizationCCOS):
        self.ccos = ccos
        self._handlers: Dict[str, Callable[..., Any]] = {
            "research.web": lambda q: {"results": [], "query": q, "note": "stub"},
            "communication.sms": lambda to, body: {"sent": False, "reason": "stub"},
            "code.repository": lambda path: {"files": [], "path": path},
        }
        for name in self._handlers:
            self.ccos.manifests.add(name)

    def invoke(self, agent_id: str, connector: str, **kwargs) -> Dict[str, Any]:
        d = self.ccos.request_capability(agent_id, connector, purpose="connector")
        if not d.approved:
            return {"ok": False, "reason": d.reason}
        action = self.ccos.authorize_action(agent_id, connector)
        if not action.approved:
            return {"ok": False, "reason": action.reason}
        handler = self._handlers.get(connector)
        if not handler:
            return {"ok": False, "reason": "no_handler"}
        try:
            return {"ok": True, "result": handler(**kwargs)}
        except TypeError:
            return {"ok": True, "result": handler(kwargs)}  # type: ignore
