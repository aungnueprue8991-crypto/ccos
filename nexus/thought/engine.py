"""Thought Engine — generate possibilities that were not explicitly requested.

Thought ≠ truth. Produces associations, analogies, counterfactuals, reframes.
Does not decide whether they are true.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Sequence

from nexus.types import Thought, ThoughtKind


class ThoughtEngine:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.stream: List[Thought] = []

    def generate(
        self,
        focus_description: str,
        domain: str = "general",
        observations: Optional[List[Dict[str, Any]]] = None,
        memory_fragments: Optional[Sequence[str]] = None,
        concepts: Optional[Sequence[str]] = None,
        mechanisms: Optional[Sequence[str]] = None,
        anomalies: Optional[Sequence[str]] = None,
        n: int = 6,
    ) -> List[Thought]:
        observations = observations or []
        memory_fragments = list(memory_fragments or [])
        concepts = list(concepts or ["energy", "structure", "flow", "constraint", "feedback"])
        mechanisms = list(mechanisms or ["heat_flow", "selection", "conservation", "compression"])
        anomalies = list(anomalies or [])

        thoughts: List[Thought] = []

        # Association
        if concepts and mechanisms:
            c = self.rng.choice(concepts)
            m = self.rng.choice(mechanisms)
            thoughts.append(
                Thought(
                    kind=ThoughtKind.ASSOCIATION,
                    content=f"'{c}' may couple with '{m}' under {focus_description[:60]}",
                    source="association",
                    salience=0.55,
                    novelty=0.45,
                    domain=domain,
                    payload={"concept": c, "mechanism": m},
                )
            )

        # Analogy across fragments / domains
        if len(memory_fragments) >= 2:
            a, b = self.rng.sample(list(memory_fragments), 2)
            thoughts.append(
                Thought(
                    kind=ThoughtKind.ANALOGY,
                    content=f"Structure of '{a[:40]}' resembles '{b[:40]}'",
                    source="analogy",
                    salience=0.6,
                    novelty=0.65,
                    domain=domain,
                    payload={"a": a, "b": b},
                )
            )
        elif concepts:
            thoughts.append(
                Thought(
                    kind=ThoughtKind.ANALOGY,
                    content=f"Domain '{domain}' may share hidden structure with selection/search landscapes",
                    source="analogy",
                    salience=0.5,
                    novelty=0.55,
                    domain=domain,
                )
            )

        # Counterfactual
        if mechanisms:
            m = self.rng.choice(mechanisms)
            thoughts.append(
                Thought(
                    kind=ThoughtKind.COUNTERFACTUAL,
                    content=f"What if mechanism '{m}' were absent or inverted?",
                    source="counterfactual",
                    salience=0.58,
                    novelty=0.6,
                    domain=domain,
                    payload={"mechanism": m},
                )
            )

        # Pattern completion
        if anomalies:
            thoughts.append(
                Thought(
                    kind=ThoughtKind.PATTERN,
                    content=f"Anomaly '{anomalies[0][:50]}' may be instance of a broader incomplete theory",
                    source="pattern_completion",
                    salience=0.7,
                    novelty=0.5,
                    domain=domain,
                )
            )

        # Recombination
        if len(concepts) >= 2:
            c1, c2 = self.rng.sample(concepts, 2)
            thoughts.append(
                Thought(
                    kind=ThoughtKind.RECOMBINATION,
                    content=f"Recombine '{c1}' + '{c2}' into a single explanatory unit",
                    source="recombination",
                    salience=0.5,
                    novelty=0.7,
                    domain=domain,
                )
            )

        # Reframe the problem
        thoughts.append(
            Thought(
                kind=ThoughtKind.REFRAME,
                content=f"Is '{focus_description[:50]}' the right problem, or a symptom of representation failure?",
                source="reframe",
                salience=0.62,
                novelty=0.55,
                domain=domain,
            )
        )

        # Surprise-linked thought from observations
        if observations or anomalies:
            thoughts.append(
                Thought(
                    kind=ThoughtKind.SURPRISE,
                    content="Prediction failure may indicate hidden variable, distribution shift, or new mechanism",
                    source="anomaly_pathway",
                    salience=0.68,
                    novelty=0.4,
                    domain=domain,
                )
            )

        # Recursive association: link two prior thoughts if stream exists
        if len(self.stream) >= 2:
            t1, t2 = self.stream[-2], self.stream[-1]
            thoughts.append(
                Thought(
                    kind=ThoughtKind.ASSOCIATION,
                    content=f"Prior thoughts may share structure: ({t1.kind.value}) ~ ({t2.kind.value})",
                    source="recursive_association",
                    salience=0.48,
                    novelty=0.5,
                    linked_ids=[t1.thought_id, t2.thought_id],
                    domain=domain,
                )
            )

        thoughts.sort(key=lambda t: t.salience * (0.5 + 0.5 * t.novelty), reverse=True)
        selected = thoughts[:n]
        self.stream.extend(selected)
        self.stream = self.stream[-100:]
        return selected
