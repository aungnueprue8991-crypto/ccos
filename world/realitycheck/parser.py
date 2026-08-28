"""Claim Parser — natural language / structured hypothesis → formal Claim."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from world.realitycheck.types import Claim, ClaimKind


class ClaimParser:
    def parse(
        self,
        text: str,
        domain: str = "general",
        source: str = "nexus",
        model_confidence: float = 0.0,
        metrics: Optional[Dict[str, float]] = None,
        baseline: Optional[Dict[str, float]] = None,
    ) -> Claim:
        metrics = dict(metrics or {})
        baseline = dict(baseline or {})
        variables: List[str] = []

        m = re.search(r"compression[^\d]*(\d+(?:\.\d+)?)\s*%", text, re.I)
        if m and "compression_ratio" not in metrics:
            metrics["compression_ratio_min"] = float(m.group(1)) / 100.0
            variables.append("compression_ratio")
        m = re.search(r"accuracy[^\d]*(?:loss)?[^\d]*(\d+(?:\.\d+)?)\s*%", text, re.I)
        if m and "accuracy_loss_max" not in metrics:
            metrics["accuracy_loss_max"] = float(m.group(1)) / 100.0
            variables.append("retrieval_accuracy")
        m = re.search(r"reduce[s]?\s+storage[^\d]*(\d+(?:\.\d+)?)\s*%", text, re.I)
        if m and "compression_ratio_min" not in metrics:
            metrics["compression_ratio_min"] = float(m.group(1)) / 100.0
            variables.append("storage")

        kind = ClaimKind.HYPOTHESIS
        if any(w in text.lower() for w in ("might", "maybe", "could", "speculate")):
            kind = ClaimKind.SPECULATION
        if metrics:
            kind = ClaimKind.HYPOTHESIS

        return Claim(
            statement=text.strip(),
            kind=kind,
            domain=domain,
            metrics=metrics,
            baseline=baseline,
            variables=variables or ["outcome"],
            source=source,
            confidence_model=model_confidence,
        )
