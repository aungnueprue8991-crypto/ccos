"""Scientific discovery engine — question → hypothesis → experiment → evidence."""

from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING

from ags.shared.types import new_id

if TYPE_CHECKING:
    from ags.models.adapter import BaseModelAdapter
    from ags.sandbox.runtime import SafeSandbox
    from ags.skills.skill import SkillRegistry


class DiscoveryEngine:
    def __init__(
        self,
        model: "BaseModelAdapter",
        sandbox: "SafeSandbox",
        skills: "SkillRegistry",
    ):
        self.model = model
        self.sandbox = sandbox
        self.skills = skills
        self.hypotheses: List[Dict[str, Any]] = []
        self.experiments: List[Dict[str, Any]] = []

    def form_hypothesis(self, question: str, context: str) -> Dict[str, Any]:
        result = self.model.structured(
            f"Form a scientific hypothesis about: {question}\n\nContext:\n{context}",
            system="Careful scientific agent. JSON only.",
            schema_hint='{"statement": str, "confidence": float, "prediction": str, "domain": str}',
        )
        hyp = {
            "id": new_id(),
            "statement": result.get("statement") or f"Hypothesis about {question}",
            "confidence": float(result.get("confidence", 0.4)),
            "prediction": result.get("prediction", ""),
            "domain": result.get("domain", "general"),
            "question": question,
        }
        self.hypotheses.append(hyp)
        self.skills.update_proficiency("form_hypothesis", 0.02)
        return hyp

    def design_experiment(self, hypothesis: Dict[str, Any]) -> Dict[str, Any]:
        plan = self.model.structured(
            f"Design a minimal experiment for: {hypothesis['statement']}",
            system="JSON experiment plan.",
            schema_hint='{"title": str, "method": str, "code": str, "expected": str}',
        )
        plan["hypothesis_id"] = hypothesis["id"]
        plan["id"] = new_id()
        self.skills.update_proficiency("design_experiment", 0.02)
        return plan

    def run_sandbox_check(self, code: str) -> Dict[str, Any]:
        if not code or not code.strip():
            code = "print([(n, n*n) for n in range(1, 6)])"
        result = self.sandbox.run_python(code)
        self.experiments.append({
            "id": result.sandbox_id,
            "success": result.success,
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:200],
        })
        if result.success:
            self.skills.update_proficiency("run_python_snippet", 0.05)
        return {
            "sandbox_id": result.sandbox_id,
            "success": result.success,
            "stdout": result.stdout[:500],
            "stderr": result.stderr[:200],
            "timed_out": result.timed_out,
        }
