"""Contradiction Discovery — preserve tensions as research opportunities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from ags.shared.types import new_id


@dataclass
class Contradiction:
    id: str = field(default_factory=new_id)
    claim_a: str = ""
    claim_b: str = ""
    note: str = ""
    resolved: bool = False
    boundary: str = ""


class ContradictionEngine:
    def __init__(self):
        self.items: List[Contradiction] = []

    def detect(self, statements: List[str]) -> List[Contradiction]:
        """Lightweight polarity detect: same subject, opposing predicates."""
        found = []
        neg = ("not", "no", "never", "false", "fails", "cannot")
        for i, a in enumerate(statements):
            for b in statements[i + 1 :]:
                al, bl = a.lower(), b.lower()
                shared = set(al.split()) & set(bl.split())
                if len(shared) < 2:
                    continue
                a_neg = any(n in al.split() for n in neg)
                b_neg = any(n in bl.split() for n in neg)
                if a_neg != b_neg:
                    c = Contradiction(claim_a=a, claim_b=b, note="polarity_conflict")
                    self.items.append(c)
                    found.append(c)
        return found

    def propose_boundary(self, c: Contradiction, boundary: str) -> Contradiction:
        c.boundary = boundary
        c.resolved = True
        return c

    def open_count(self) -> int:
        return sum(1 for c in self.items if not c.resolved)
