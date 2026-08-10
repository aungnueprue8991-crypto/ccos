"""CapabilityInvoker — the only path from intent to external effect."""

from __future__ import annotations

from typing import Optional

from constitution.schemas.capability import CapabilityResult, CapabilityObservation
from constitution.schemas.invocation import InvocationEnvelope, AuthorizationDecision
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger
from capabilities.gate.execution_gate import ExecutionGate
from capabilities.adapters.base import CapabilityAdapter


class CapabilityInvoker:
    def __init__(self, gate: ExecutionGate, ledger: EventLedger):
        self.gate = gate
        self.ledger = ledger

    def invoke(self, invocation: InvocationEnvelope, adapter: CapabilityAdapter):
        decision = self.gate.authorize(invocation)
        if not decision.allowed:
            result = CapabilityResult(
                capability_id=invocation.capability_id, success=False,
                error=f"denied: {decision.reason}", provenance=list(invocation.provenance),
            )
            self.ledger.append(EventEnvelope(
                event_type="capability.invocation.completed", producer_id="cos.invoker",
                payload={"invocation_id": invocation.invocation_id, "allowed": False, "reason": decision.reason},
            ))
            return decision, result
        if hasattr(adapter, "execute_authorized"):
            result = adapter.execute_authorized(invocation.input_payload, decision)
        else:
            result = adapter.execute(invocation.input_payload, sandboxed=True)
        result.capability_id = invocation.capability_id
        result.provenance = list(result.provenance) + [invocation.invocation_id, decision.decision_id]
        obs = CapabilityObservation(
            capability_id=invocation.capability_id, result_id=result.result_id,
            metrics={"duration_ms": result.duration_ms, "success": 1.0 if result.success else 0.0},
            verified=result.success,
        )
        result.observation_ids = [obs.observation_id]
        self.ledger.append(EventEnvelope(
            event_type="capability.invocation.completed", producer_id="cos.invoker",
            payload={"invocation_id": invocation.invocation_id, "capability_id": invocation.capability_id,
                     "allowed": True, "success": result.success, "duration_ms": result.duration_ms,
                     "observation_id": obs.observation_id, "input_hash": invocation.input_hash,
                     "authorization_id": decision.decision_id},
            provenance=result.provenance, correlation_id=invocation.correlation_id,
        ))
        return decision, result
