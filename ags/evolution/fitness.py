"""Fitness evaluation helpers."""
from __future__ import annotations
from typing import Any, Dict
from ags.evolution.reproduction import FitnessVector

def evaluate_agent_metrics(metrics: Dict[str, Any]) -> FitnessVector:
    return FitnessVector(
        learning=min(1.0, float(metrics.get("knowledge", 0)) / 10.0),
        discovery=min(1.0, float(metrics.get("discoveries", 0)) / 5.0),
        cooperation=min(1.0, float(metrics.get("social_links", 0)) / 5.0),
        prediction=float(metrics.get("prediction_accuracy", 0.5)),
        scientific_reliability=float(metrics.get("verification_rate", 0.5)),
        resource_efficiency=float(metrics.get("resource_efficiency", 0.5)),
        adaptability=float(metrics.get("adaptability", 0.5)),
        constitutional_compliance=1.0 if metrics.get("ledger_valid", True) else 0.0,
    )

def pareto_front(vectors: Dict[str, FitnessVector]) -> list:
    """Return agent ids on simple Pareto front (maximizing all)."""
    ids = list(vectors.keys())
    front = []
    for i in ids:
        dominated = False
        for j in ids:
            if i != j and vectors[i].dominated_by(vectors[j]):
                dominated = True
                break
        if not dominated:
            front.append(i)
    return front
