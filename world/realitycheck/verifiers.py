"""Code / benchmark / reproduction / adversarial verifiers."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class CodeVerifier:
    """Run a callable and capture metrics or exception."""

    def run(self, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        try:
            out = fn()
            if not isinstance(out, dict):
                return {"ok": False, "error": "non_dict_result", "raw": str(out)}
            out = dict(out)
            out.setdefault("ok", True)
            return out
        except Exception as e:
            return {"ok": False, "error": type(e).__name__, "message": str(e)}


class BenchmarkEngine:
    def compare(
        self,
        observed: Dict[str, Any],
        expected: Dict[str, Any],
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        thresholds = thresholds or {}
        mismatches = []
        for k, exp_v in expected.items():
            if k not in observed:
                mismatches.append({"key": k, "reason": "missing"})
                continue
            thr = thresholds.get(k)
            if thr is not None:
                try:
                    if abs(float(observed[k]) - float(exp_v)) > float(thr):
                        mismatches.append(
                            {
                                "key": k,
                                "observed": observed[k],
                                "expected": exp_v,
                                "threshold": thr,
                            }
                        )
                except (TypeError, ValueError):
                    if observed[k] != exp_v:
                        mismatches.append(
                            {"key": k, "observed": observed[k], "expected": exp_v}
                        )
            elif observed[k] != exp_v:
                mismatches.append(
                    {"key": k, "observed": observed[k], "expected": exp_v}
                )
        return {"pass": len(mismatches) == 0, "mismatches": mismatches}


class ReproductionEngine:
    def reproduce(
        self,
        fn: Callable[[], Dict[str, Any]],
        times: int = 2,
    ) -> Dict[str, Any]:
        runs = []
        for _ in range(max(1, times)):
            runs.append(CodeVerifier().run(fn))
        oks = [r.get("ok") for r in runs]
        return {"runs": runs, "all_ok": all(oks), "n": len(runs)}


class AdversarialVerifier:
    """Attempt to falsify: if attack_fn returns truthy, claim is challenged."""

    def attack(self, attack_fn: Callable[[], Any]) -> Dict[str, Any]:
        try:
            result = attack_fn()
            return {"challenged": bool(result), "result": result}
        except Exception as e:
            return {"challenged": False, "error": str(e)}
