"""Causal engine — competing models, intervention proposals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ags.shared.types import new_id


@dataclass
class CausalModel:
    model_id: str = field(default_factory=new_id)
    description: str = ""
    edges: List[tuple] = field(default_factory=list)
    prior: float = 0.5
    posterior: float = 0.5


class CausalEngine:
    def __init__(self):
        self.models: List[CausalModel] = []

    def propose_models(self, x: str, y: str, confound: str = "Z") -> List[CausalModel]:
        models = [
            CausalModel(description=f"{x} → {y}", edges=[(x, y)], prior=0.34),
            CausalModel(
                description=f"{confound} → {x}, {confound} → {y}",
                edges=[(confound, x), (confound, y)],
                prior=0.33,
            ),
            CausalModel(description=f"{x} ↔ {y}", edges=[(x, y), (y, x)], prior=0.33),
        ]
        self.models = models
        return models

    def distinguishing_intervention(self, models: Optional[List[CausalModel]] = None) -> Dict[str, str]:
        models = models or self.models
        if not models:
            return {"intervene_on": "X", "observe": "Y", "rationale": "default"}
        top = max(models, key=lambda m: m.posterior)
        if top.edges:
            cause, effect = top.edges[0]
            return {
                "intervene_on": cause,
                "observe": effect,
                "rationale": f"distinguish models; top={top.description}",
            }
        return {"intervene_on": "X", "observe": "Y", "rationale": "fallback"}

    def update_posterior(self, model_id: str, likelihood: float) -> None:
        for m in self.models:
            if m.model_id == model_id:
                m.posterior = max(0.01, min(0.99, 0.5 * m.posterior + 0.5 * likelihood))
