"""Living-lineage genome (dict-based)."""

from __future__ import annotations

import copy
import json
import random
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


def load_default(path: Optional[str] = None) -> Dict[str, Any]:
    p = Path(path or "genomes/default_genome.json")
    if p.exists():
        return json.loads(p.read_text())
    return {
        "genome_id": "GEN-BASE",
        "parents": [],
        "lineage": ["GEN-BASE"],
        "motivation_drive_weights": {"curiosity": 0.8, "reproduction": 0.35},
        "fixed_parameters": {"autonomy_seeking": 0.7, "learning_rate_modifier": 0.8},
        "personality_traits": {"curiosity": 0.7, "persistence": 0.6},
    }


def mutate(parent: Dict[str, Any]) -> Dict[str, Any]:
    child = copy.deepcopy(parent)
    child["genome_id"] = f"GEN-{uuid.uuid4().hex[:8]}"
    child["parents"] = [parent.get("genome_id", "unknown")]
    child["lineage"] = list(parent.get("lineage") or []) + [child["genome_id"]]
    for key in list(child.get("motivation_drive_weights", {}).keys()):
        child["motivation_drive_weights"][key] = max(
            0.05,
            min(0.99, child["motivation_drive_weights"][key] * random.uniform(0.9, 1.1)),
        )
    fp = child.setdefault("fixed_parameters", {})
    for key in ("autonomy_seeking", "learning_rate_modifier", "hypothesis_creativity"):
        if key in fp and isinstance(fp[key], (int, float)):
            fp[key] = max(0.05, min(0.99, fp[key] * random.uniform(0.95, 1.05)))
    return child


def crossover(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    child = copy.deepcopy(a)
    child["genome_id"] = f"GEN-{uuid.uuid4().hex[:8]}"
    child["parents"] = [a.get("genome_id"), b.get("genome_id")]
    child["lineage"] = list(
        dict.fromkeys((a.get("lineage") or []) + (b.get("lineage") or []) + [child["genome_id"]])
    )
    for key in child.get("motivation_drive_weights", {}):
        if key in b.get("motivation_drive_weights", {}):
            child["motivation_drive_weights"][key] = (
                a["motivation_drive_weights"][key] + b["motivation_drive_weights"][key]
            ) / 2
    return child
