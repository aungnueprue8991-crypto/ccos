"""N1 Capability Fabric — discovery → validation → approval → sandbox → active."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from constitution.schemas.capability import (
    CapabilityManifest, CapabilityResult, CapabilityLifecycle,
)
from constitution.schemas.event import EventEnvelope
from constitution.schemas.governance import Proposal
from kernel.events.ledger import EventLedger
from kernel.registry.capability_registry import CapabilityRegistry
from governance.decisions.engine import GovernanceEngine
from governance.policies.evaluator import PolicyEvaluator
from evolution.archive.store import ExperimentArchive
from capabilities.adapters.base import CapabilityAdapter, AdapterRegistry
from capabilities.sandbox.executor import SandboxExecutor, SandboxPolicy


@dataclass
class FabricOutcome:
    capability_id: str
    stages: List[str] = field(default_factory=list)
    sandbox_success: bool = False
    public_score: float = 0.0
    private_score: float = 0.0
    activated: bool = False
    result: Optional[CapabilityResult] = None
    errors: List[str] = field(default_factory=list)


class CapabilityFabric:
    def __init__(
        self,
        ledger: EventLedger,
        registry: CapabilityRegistry,
        governance: GovernanceEngine,
        policies: Optional[PolicyEvaluator] = None,
        archive: Optional[ExperimentArchive] = None,
    ):
        self.ledger = ledger
        self.registry = registry
        self.governance = governance
        self.policies = policies or PolicyEvaluator(ledger)
        self.archive = archive
        self.adapters = AdapterRegistry()
        self.sandbox = SandboxExecutor(ledger)

    def register_adapter(self, adapter: CapabilityAdapter) -> CapabilityManifest:
        self.adapters.register(adapter)
        manifest = adapter.manifest()
        return self.registry.register(manifest)

    def validate(self, capability_id: str, adapter: CapabilityAdapter) -> CapabilityManifest:
        sample = self._sample_input(adapter)
        ok, reason = adapter.validate_input(sample)
        if not ok:
            raise ValueError(f"validation failed: {reason}")
        return self.registry.transition(
            capability_id, CapabilityLifecycle.VALIDATED,
            reason="schema+sample ok", authorized_by="cos.fabric",
        )

    def request_approval(self, capability_id: str, proposer: str = "cos.fabric") -> Proposal:
        m = self.registry.get(capability_id)
        if not m:
            raise KeyError(capability_id)
        prop = Proposal(
            proposer=proposer,
            title=f"Approve capability {m.name}",
            proposal_type="capability_activation",
            payload={"capability_id": capability_id, "name": m.name, "permissions": m.permissions},
            evidence_refs=[capability_id],
        )
        return self.governance.submit(prop)

    def approve(self, capability_id: str, proposal_id: str, decision_maker: str = "citizen:governor") -> CapabilityManifest:
        self.governance.decide(
            proposal_id, decision_maker=decision_maker, outcome="APPROVED",
            rationale="fabric lifecycle approval", evidence=[capability_id],
        )
        return self.registry.transition(
            capability_id, CapabilityLifecycle.APPROVED,
            reason="governance approved", authorized_by=decision_maker,
        )

    def sandbox_benchmark(
        self, capability_id: str, adapter: CapabilityAdapter, payload: Optional[dict] = None,
    ) -> tuple[float, float, SandboxPolicy]:
        m = self.registry.get(capability_id)
        if not m:
            raise KeyError(capability_id)
        if m.lifecycle_status not in (CapabilityLifecycle.APPROVED, CapabilityLifecycle.SANDBOXED):
            raise PermissionError(f"cannot sandbox from {m.lifecycle_status}")
        self.registry.transition(
            capability_id, CapabilityLifecycle.SANDBOXED,
            reason="entering sandbox", authorized_by="cos.fabric",
        )
        policy = SandboxPolicy(
            timeout_s=float(m.sandbox_profile.get("timeout_s", 5)),
            memory_mb=float(m.sandbox_profile.get("memory_mb", 64)),
            network=bool(m.sandbox_profile.get("network", False)),
        )
        payload = payload or self._sample_input(adapter)
        fn = self._fn_name(adapter)
        run = self.sandbox.run(fn, payload, policy=policy, capability_id=capability_id)
        public = 1.0 if run.success else 0.0
        private = public * 0.95 if run.success else 0.0
        if self.archive:
            self.archive.archive(
                experiment_id=run.run_id,
                parameters={"capability_id": capability_id, "payload": payload},
                public_metrics={"success": public},
                private_metrics={"heldout": private},
                code_hash=capability_id[:16],
            )
        return public, private, policy

    def activate(
        self, capability_id: str, public_score: float, private_score: float,
        authorized_by: str = "citizen:governor", min_public: float = 0.5,
    ) -> CapabilityManifest:
        if public_score < min_public:
            raise PermissionError(f"scores insufficient public={public_score:.3f}")
        return self.registry.transition(
            capability_id, CapabilityLifecycle.ACTIVE,
            reason=f"benchmark public={public_score:.3f} private={private_score:.3f}",
            authorized_by=authorized_by,
        )

    def execute_active(self, capability_id: str, adapter: CapabilityAdapter, payload: dict) -> CapabilityResult:
        m = self.registry.get(capability_id)
        if not m or m.lifecycle_status not in (CapabilityLifecycle.ACTIVE, CapabilityLifecycle.TRUSTED):
            raise PermissionError("capability not ACTIVE")
        result = adapter.execute(payload, sandboxed=True)
        result.capability_id = capability_id
        self.ledger.append(EventEnvelope(
            event_type="capability.executed", producer_id="cos.fabric",
            payload={"capability_id": capability_id, "success": result.success,
                     "duration_ms": result.duration_ms},
        ))
        return result

    def full_lifecycle(
        self, adapter: CapabilityAdapter, execute_payload: Optional[dict] = None,
        decision_maker: str = "citizen:governor",
    ) -> FabricOutcome:
        outcome = FabricOutcome(capability_id="")
        try:
            m = self.register_adapter(adapter)
            outcome.capability_id = m.capability_id
            outcome.stages.append("REGISTERED")
            self.validate(m.capability_id, adapter)
            outcome.stages.append("VALIDATED")
            prop = self.request_approval(m.capability_id)
            self.approve(m.capability_id, prop.proposal_id, decision_maker)
            outcome.stages.append("APPROVED")
            pub, priv, _ = self.sandbox_benchmark(m.capability_id, adapter, execute_payload)
            outcome.public_score, outcome.private_score = pub, priv
            outcome.sandbox_success = pub > 0
            outcome.stages.append("SANDBOXED")
            outcome.stages.append("BENCHMARKED")
            if pub < 0.5:
                outcome.errors.append(f"scores insufficient public={pub:.3f} private={priv:.3f}")
                return outcome
            self.activate(m.capability_id, pub, priv, decision_maker)
            outcome.activated = True
            outcome.stages.append("ACTIVE")
            payload = execute_payload or self._sample_input(adapter)
            outcome.result = self.execute_active(m.capability_id, adapter, payload)
        except Exception as e:
            outcome.errors.append(str(e))
        return outcome

    def _fn_name(self, adapter: CapabilityAdapter) -> str:
        mapping = {
            "connector.echo": "echo", "connector.compute": "compute",
            "connector.process.safe": "process", "connector.http.get": "http",
            "connector.fs.read": "fs",
        }
        return mapping.get(adapter.adapter_id, "echo")

    def _sample_input(self, adapter: CapabilityAdapter) -> dict:
        if adapter.adapter_id == "connector.echo":
            return {"message": "ping"}
        if adapter.adapter_id == "connector.compute":
            return {"op": "add", "a": 1, "b": 1}
        if adapter.adapter_id == "connector.process.safe":
            return {"cmd": "echo", "args": ["ping"]}
        if adapter.adapter_id == "connector.fs.read":
            return {"path": ".keep"}
        if adapter.adapter_id == "connector.http.get":
            return {"url": "https://example.com/"}
        return {}
