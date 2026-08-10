"""N3.2 Execution Gate — authorization before any side effect.

Adapter authentication ≠ capability admissibility ≠ invocation authorization ≠ execution.
Adapters never call authorize(); they receive an AuthorizationDecision.
"""

from __future__ import annotations

from typing import Any, Optional

from constitution.schemas.capability import CapabilityLifecycle, CapabilityPermission
from constitution.schemas.invocation import (
    InvocationEnvelope, AuthorizationDecision, RiskClass,
)
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger
from kernel.registry.capability_registry import CapabilityRegistry
from kernel.security.authorization import AuthorizationService
from kernel.resources.manager import ResourceManager, Quota

_PERM_RISK = {
    CapabilityPermission.READ_ONLY.value: RiskClass.LOW,
    CapabilityPermission.COMPUTE.value: RiskClass.LOW,
    CapabilityPermission.READ_FILE.value: RiskClass.MEDIUM,
    CapabilityPermission.WRITE_FILE.value: RiskClass.HIGH,
    CapabilityPermission.READ_WEB.value: RiskClass.MEDIUM,
    CapabilityPermission.NETWORK_ACCESS.value: RiskClass.HIGH,
    CapabilityPermission.EXECUTE_CODE.value: RiskClass.CRITICAL,
    CapabilityPermission.DEPLOY.value: RiskClass.CRITICAL,
    CapabilityPermission.MEMORY_WRITE.value: RiskClass.MEDIUM,
}


class ExecutionGate:
    def __init__(self, ledger: EventLedger, registry: CapabilityRegistry,
                 auth: Optional[AuthorizationService] = None,
                 resources: Optional[ResourceManager] = None):
        self.ledger = ledger
        self.registry = registry
        self.auth = auth or AuthorizationService(ledger)
        self.resources = resources or ResourceManager(ledger)

    def authorize(self, invocation: InvocationEnvelope) -> AuthorizationDecision:
        inv = invocation.bind_input()
        steps: list[str] = []
        manifest = self.registry.get(inv.capability_id)
        if not manifest:
            return self._deny(inv, "capability not found", steps)
        steps.append("registry_lookup")
        if manifest.lifecycle_status not in (CapabilityLifecycle.ACTIVE, CapabilityLifecycle.TRUSTED):
            return self._deny(inv, f"lifecycle {manifest.lifecycle_status.value} not executable", steps)
        steps.append("lifecycle_ok")
        risk = self._assess_risk(manifest.permissions)
        if risk in (RiskClass.HIGH, RiskClass.CRITICAL) and not inv.intent_id:
            return self._deny(inv, "HIGH/CRITICAL risk requires intent_id", steps)
        steps.append("intent_binding")
        if not inv.issuer:
            return self._deny(inv, "issuer required", steps)
        steps.append("issuer_ok")
        subject = inv.agent_id or inv.issuer
        mem = float(inv.resource_policy.get("memory_mb", 64))
        cpu = float(inv.resource_policy.get("cpu", 1.0))
        if not self.resources.allocate(subject, cpu=cpu, memory_mb=mem):
            return self._deny(inv, "resource quota exceeded", steps)
        steps.append("resources_ok")
        token = self.auth.authorize(subject=inv.issuer, action="execute",
                                    resource=inv.capability_id, intent_id=inv.intent_id)
        steps.append("authorized")
        decision = AuthorizationDecision(
            allowed=True, reason="all gates passed: " + " → ".join(steps),
            capability_id=inv.capability_id, invocation_id=inv.invocation_id,
            permissions_granted=list(manifest.permissions),
            resource_limits={"cpu": cpu, "memory_mb": mem}, risk_class=risk,
        )
        inv.authorization_id = decision.decision_id
        self.ledger.append(EventEnvelope(
            event_type="capability.invocation.authorized", producer_id="cos.execution_gate",
            payload={"invocation_id": inv.invocation_id, "capability_id": inv.capability_id,
                     "decision_id": decision.decision_id, "issuer": inv.issuer,
                     "intent_id": inv.intent_id, "risk": risk.value, "auth_token": token,
                     "input_hash": inv.input_hash},
            correlation_id=inv.correlation_id, provenance=inv.provenance,
        ))
        return decision

    def _deny(self, inv: InvocationEnvelope, reason: str, steps: list[str]) -> AuthorizationDecision:
        self.ledger.append(EventEnvelope(
            event_type="capability.invocation.denied", producer_id="cos.execution_gate",
            payload={"invocation_id": inv.invocation_id, "capability_id": inv.capability_id,
                     "reason": reason, "steps": steps, "issuer": inv.issuer},
            correlation_id=inv.correlation_id,
        ))
        return AuthorizationDecision(allowed=False, reason=reason,
                                     capability_id=inv.capability_id, invocation_id=inv.invocation_id)

    def _assess_risk(self, permissions: list[str]) -> RiskClass:
        order = [RiskClass.LOW, RiskClass.MEDIUM, RiskClass.HIGH, RiskClass.CRITICAL]
        level = RiskClass.LOW
        for p in permissions:
            r = _PERM_RISK.get(p, RiskClass.MEDIUM)
            if order.index(r) > order.index(level):
                level = r
        return level
