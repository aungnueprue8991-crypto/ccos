"""COG Reasoning Backend — pluggable LLM + deterministic local reasoner.

Production interface: never treats model output as truth (CCOS-003).
Outputs are hypotheses / plans that must pass evidence + governance gates.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from constitution.schemas.event import EventEnvelope, EpistemicStatus
from kernel.events.ledger import EventLedger


@dataclass
class ReasoningResult:
    result_id: str = field(default_factory=lambda: str(uuid4()))
    kind: str = "hypothesis"
    content: str = ""
    structured: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    epistemic_status: EpistemicStatus = EpistemicStatus.UNVERIFIED
    model_id: str = "local"
    prompt_hash: str = ""
    provenance: List[str] = field(default_factory=list)


class ReasoningBackend(ABC):
    @abstractmethod
    def reason(self, prompt: str, context: Dict[str, Any] | None = None) -> ReasoningResult:
        ...


class DeterministicReasoner(ReasoningBackend):
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger
        self.model_id = "deterministic-v1"

    def reason(self, prompt: str, context: Dict[str, Any] | None = None) -> ReasoningResult:
        context = context or {}
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        lower = prompt.lower()
        kind = "hypothesis"
        if "plan" in lower or "how to" in lower:
            kind = "plan"
        elif "critique" in lower or "review" in lower:
            kind = "critique"
        elif "analy" in lower:
            kind = "analysis"
        structured = {
            "summary": prompt[:200],
            "context_keys": list(context.keys()),
            "suggested_actions": [],
            "assumptions": ["model output is unverified"],
        }
        if kind == "plan":
            structured["suggested_actions"] = [
                "gather evidence", "form hypothesis", "run experiment", "submit to governance",
            ]
        result = ReasoningResult(
            kind=kind,
            content=f"[{self.model_id}] Structured response for: {prompt[:80]}...",
            structured=structured,
            confidence=0.4,
            epistemic_status=EpistemicStatus.UNVERIFIED,
            model_id=self.model_id,
            prompt_hash=prompt_hash,
            provenance=list(context.get("evidence_ids", [])),
        )
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="cog.reasoning.completed", producer_id="cog.reasoning",
                payload={
                    "result_id": result.result_id, "kind": kind, "model_id": self.model_id,
                    "confidence": result.confidence,
                    "epistemic_status": result.epistemic_status.value,
                    "prompt_hash": prompt_hash,
                },
            ))
        return result


class HTTPReasoner(ReasoningBackend):
    def __init__(self, url: str, ledger: Optional[EventLedger] = None, timeout: float = 30.0):
        self.url = url
        self.ledger = ledger
        self.timeout = timeout
        self.fallback = DeterministicReasoner(ledger)
        self.model_id = f"http:{url}"

    def reason(self, prompt: str, context: Dict[str, Any] | None = None) -> ReasoningResult:
        try:
            import httpx
            r = httpx.post(self.url, json={"prompt": prompt, "context": context or {}}, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
            result = ReasoningResult(
                kind=data.get("kind", "analysis"),
                content=data.get("content", ""),
                structured=data.get("structured", {}),
                confidence=float(data.get("confidence", 0.3)),
                epistemic_status=EpistemicStatus.UNVERIFIED,
                model_id=data.get("model_id", self.model_id),
                prompt_hash=prompt_hash,
                provenance=list((context or {}).get("evidence_ids", [])),
            )
            if self.ledger:
                self.ledger.append(EventEnvelope(
                    event_type="cog.reasoning.completed", producer_id="cog.reasoning",
                    payload={
                        "result_id": result.result_id, "kind": result.kind,
                        "model_id": result.model_id, "confidence": result.confidence,
                        "epistemic_status": "UNVERIFIED",
                    },
                ))
            return result
        except Exception:
            return self.fallback.reason(prompt, context)
