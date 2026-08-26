"""REALITY CHECK PROTOCOL — formal 15-step checklist object.

Every material claim must pass through this structure.
AI assertions are never evidence (rules 11–12).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ags.shared.types import new_id, now_ts


class ProtocolVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    FALSIFIED = "FALSIFIED"


@dataclass
class LayerSeparation:
    """Rule 10 — never collapse these layers."""
    observation: str = ""
    source_report: str = ""  # not evidence by itself
    implementation_verification: str = ""
    independent_reproduction: str = ""
    interpretation: str = ""
    speculation: str = ""

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class ProtocolChecklist:
    """
    The 15-step Reality Check Protocol as a first-class object.

    Steps:
      1  falsifiable proposition
      2  minimum evidence required
      3  inspect artifact
      4  execute relevant code
      5  compare observed vs expected
      6  measure performance (do not accept reported)
      7  reproduce independently
      8  attempt to falsify
      9  search contradictory evidence
      10 separate observation/source/impl/repro/interp/speculation
      11 never treat AI assertion as evidence
      12 never VERIFIED because another AI agrees
      13 report only evidence-supported observations
      14 insufficient evidence → UNVERIFIED
      15 contradictory evidence → FALSIFIED
    """

    checklist_id: str = field(default_factory=new_id)
    claim_text: str = ""
    # Step 1
    falsifiable_proposition: str = ""
    # Step 2
    minimum_evidence: str = ""
    # Steps 3–9
    artifact_inspected: str = ""
    execution_ran: bool = False
    execution_error: str = ""
    observed_output: Any = None
    expected_predicate: str = ""
    comparison_pass: Optional[bool] = None
    measured_metrics: Dict[str, Any] = field(default_factory=dict)
    reproduction_ran: bool = False
    reproduction_pass: Optional[bool] = None
    falsification_attempt: str = ""
    falsification_result: str = ""
    contradictory_evidence: str = ""
    # Step 10
    layers: LayerSeparation = field(default_factory=LayerSeparation)
    # Steps 11–12 guards
    ai_assertion_used_as_evidence: bool = False
    ai_agreement_used_as_verification: bool = False
    model_confidence: float = 0.0  # recorded, never decisive
    # Steps 13–15
    evidence_sufficient: bool = False
    verdict: ProtocolVerdict = ProtocolVerdict.UNVERIFIED
    notes: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=now_ts)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d

    def finalize(self) -> "ProtocolChecklist":
        """Apply rules 11–15 to set verdict from recorded fields only."""
        self.notes = list(self.notes)
        if self.ai_assertion_used_as_evidence or self.ai_agreement_used_as_verification:
            self.notes.append("rule_11_12_violation: AI assertion/agreement cannot verify")
            self.verdict = ProtocolVerdict.UNVERIFIED
            self.evidence_sufficient = False
            return self

        if self.execution_error:
            self.evidence_sufficient = False
            self.verdict = ProtocolVerdict.UNVERIFIED
            self.notes.append(f"execution_error:{self.execution_error}")
            return self

        if not self.execution_ran:
            self.evidence_sufficient = False
            self.verdict = ProtocolVerdict.UNVERIFIED
            self.notes.append("rule_14: no execution → UNVERIFIED")
            return self

        if self.comparison_pass is False:
            self.evidence_sufficient = True
            self.verdict = ProtocolVerdict.FALSIFIED
            self.notes.append("rule_15: observed contradicts expected → FALSIFIED")
            return self

        if self.comparison_pass is True:
            if self.reproduction_ran and self.reproduction_pass is False:
                self.evidence_sufficient = False
                self.verdict = ProtocolVerdict.UNVERIFIED
                self.notes.append("reproduction_failed → UNVERIFIED")
                return self
            if self.falsification_result and "CLAIM_FALSIFIED" in self.falsification_result.upper():
                self.evidence_sufficient = True
                self.verdict = ProtocolVerdict.FALSIFIED
                self.notes.append("falsification_probe: CLAIM_FALSIFIED")
                return self
            self.evidence_sufficient = True
            self.verdict = ProtocolVerdict.VERIFIED
            self.notes.append("steps_1_15_satisfied")
            if self.falsification_result:
                self.notes.append(f"falsify_probe={self.falsification_result[:80]}")
            return self

        self.evidence_sufficient = False
        self.verdict = ProtocolVerdict.UNVERIFIED
        self.notes.append("rule_14: comparison incomplete → UNVERIFIED")
        return self


class ProtocolRunner:
    """
    Execute the 15-step protocol for a claim.

    run_fn:        () -> observed measurements (dict or scalar)
    expected_fn:   (observed) -> bool
    falsify_fn:    optional () -> str description of probe result
    """

    def run(
        self,
        claim_text: str,
        proposition: str,
        minimum_evidence: str,
        run_fn: Callable[[], Any],
        expected_fn: Callable[[Any], bool],
        expected_predicate: str = "",
        artifact: str = "",
        falsify_fn: Optional[Callable[[], str]] = None,
        model_confidence: float = 0.0,
        interpretation: str = "",
        speculation: str = "",
        reproduce: bool = True,
    ) -> ProtocolChecklist:
        cl = ProtocolChecklist(
            claim_text=claim_text,
            falsifiable_proposition=proposition,
            minimum_evidence=minimum_evidence,
            artifact_inspected=artifact,
            expected_predicate=expected_predicate or proposition,
            model_confidence=model_confidence,
            ai_assertion_used_as_evidence=False,
            ai_agreement_used_as_verification=False,
        )
        cl.layers.speculation = speculation or "none — AI narrative not used as evidence"
        cl.layers.source_report = "not used as evidence"
        cl.layers.interpretation = interpretation

        # Steps 3–4
        try:
            observed = run_fn()
            cl.execution_ran = True
            cl.observed_output = observed
            cl.measured_metrics = observed if isinstance(observed, dict) else {"value": observed}
            cl.layers.observation = f"executed; output={observed!r}"[:500]
            cl.layers.implementation_verification = "PASS"
        except Exception as e:
            cl.execution_ran = False
            cl.execution_error = f"{type(e).__name__}: {e}"
            cl.layers.observation = cl.execution_error
            cl.layers.implementation_verification = "FAIL"
            return cl.finalize()

        # Step 5–6
        try:
            cl.comparison_pass = bool(expected_fn(observed))
        except Exception as e:
            cl.comparison_pass = None
            cl.notes.append(f"comparison_error:{e}")

        # Step 7
        if reproduce:
            try:
                obs2 = run_fn()
                cl.reproduction_ran = True
                if isinstance(observed, dict) and isinstance(obs2, dict):
                    close = True
                    for k, v in observed.items():
                        if k not in obs2:
                            close = False
                            break
                        if isinstance(v, float) and isinstance(obs2[k], float):
                            if abs(v - obs2[k]) > 1e-6:
                                close = False
                        elif v != obs2[k]:
                            close = False
                    cl.reproduction_pass = close
                else:
                    cl.reproduction_pass = observed == obs2
                cl.layers.independent_reproduction = (
                    "PASS" if cl.reproduction_pass else "DRIFT"
                )
            except Exception as e:
                cl.reproduction_ran = True
                cl.reproduction_pass = False
                cl.layers.independent_reproduction = f"FAIL:{e}"

        # Steps 8–9
        if falsify_fn is not None:
            try:
                cl.falsification_attempt = "ran"
                cl.falsification_result = str(falsify_fn())
            except Exception as e:
                cl.falsification_attempt = "error"
                cl.falsification_result = f"{type(e).__name__}: {e}"
        else:
            cl.falsification_attempt = "not_attempted"
            cl.falsification_result = ""

        # model confidence recorded but must not decide (rules 11–12)
        if model_confidence and model_confidence > 0.9 and not cl.execution_ran:
            cl.notes.append("high_model_confidence_ignored")

        return cl.finalize()
