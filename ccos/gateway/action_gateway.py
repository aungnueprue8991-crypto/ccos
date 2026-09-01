"""Action gateway — every tool call goes through policy."""
from __future__ import annotations
import time, uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

@dataclass
class ActionDecision:
    request_id: str
    tool_id: str
    decision: str
    risk_level: int
    reason: str
    policy_action: str
    agent_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_event(self) -> Dict[str, Any]:
        return {
            "event_id": f"EV-{uuid.uuid4().hex[:12]}",
            "event_type": "action.decision" if self.decision != "denied" else "action.denied",
            "request_id": self.request_id,
            "tool_id": self.tool_id,
            "decision": self.decision,
            "risk_level": self.risk_level,
            "reason": self.reason,
            "policy_action": self.policy_action,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
        }

class ActionGateway:
    def __init__(self, matrix_path: Optional[str] = None, emergency_stop: bool = False) -> None:
        root = Path(__file__).resolve().parents[2]
        path = Path(matrix_path) if matrix_path else root / "contracts" / "policy_matrix.yaml"
        self.matrix = yaml.safe_load(path.read_text()) if path.exists() else {"tools": {}, "default": "deny"}
        self.emergency_stop = emergency_stop
        self.history: List[ActionDecision] = []
        self.approval_queue: List[Dict[str, Any]] = []

    def submit(self, tool_id: str, context: Optional[Dict[str, Any]] = None) -> ActionDecision:
        context = context or {}
        request_id = context.get("request_id") or f"REQ-{uuid.uuid4().hex[:10]}"
        agent_id = context.get("agent_id")
        if self.emergency_stop:
            d = ActionDecision(request_id, tool_id, "denied", 99, "emergency_stop", "block", agent_id)
            self.history.append(d)
            return d
        tool = self.matrix.get("tools", {}).get(tool_id)
        if not tool:
            d = ActionDecision(request_id, tool_id, "denied", 99, "unknown_tool", self.matrix.get("default", "deny"), agent_id)
            self.history.append(d)
            return d
        risk = int(tool.get("risk", 99))
        policy_action = tool.get("action", "deny")
        threshold = int(self.matrix.get("approval_threshold", 6))
        if policy_action == "approval_required" or risk >= threshold:
            d = ActionDecision(request_id, tool_id, "approval_required", risk, "risk_or_policy_requires_approval", policy_action, agent_id)
            self.approval_queue.append({"request_id": request_id, "tool_id": tool_id, "risk": risk})
        elif policy_action in ("auto", "auto_audit", "sandbox_required", "realitycheck_required"):
            d = ActionDecision(request_id, tool_id, "allowed", risk, f"policy={policy_action}", policy_action, agent_id)
        else:
            d = ActionDecision(request_id, tool_id, "denied", risk, f"policy={policy_action}", policy_action, agent_id)
        self.history.append(d)
        return d

    def coverage(self) -> Dict[str, Any]:
        total = len(self.history)
        return {
            "total_decisions": total,
            "allowed": sum(1 for d in self.history if d.decision == "allowed"),
            "denied": sum(1 for d in self.history if d.decision == "denied"),
            "approval_required": sum(1 for d in self.history if d.decision == "approval_required"),
            "coverage_pct": 100.0 if total > 0 else 0.0,
        }
