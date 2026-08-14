"""AGS v1.4 — Scientific Research Civilization substrate.

Persistent programs, agenda, hypothesis competition, experiment archive,
peer review, failed-hypothesis archive, knowledge graph.
REPRODUCTION remains DENIED (evolution gate not opened).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ags.shared.types import new_id, now_ts
from ags.v12.teaching import KnowledgePacket, TeachingProtocol, SocialEpistemicMemory, BeliefState
from ags.collaboration.team import CollaborationCoordinator, ResearchProblem, Role


@dataclass
class ResearchQuestion:
    question_id: str
    text: str
    domain: str
    priority: float = 0.5
    source: str = "frontier"  # prediction_error | gap | contradiction | anomaly | peer | frontier
    status: str = "open"


@dataclass
class HypothesisRecord:
    hypothesis_id: str
    question_id: str
    statement: str
    author_id: str
    confidence: float = 0.4
    status: str = "active"  # active | supported | falsified | archived
    predictions: List[str] = field(default_factory=list)
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)


@dataclass
class ExperimentRecord:
    experiment_id: str
    hypothesis_id: str
    researcher_id: str
    environment: str
    inputs: Dict[str, Any]
    procedure: str
    capability_requirements: List[str]
    output: Dict[str, Any]
    evidence_hash: str
    result: str  # success | failure | inconclusive
    reproducible: bool = True
    timestamp: float = field(default_factory=now_ts)


@dataclass
class ResearchProgram:
    program_id: str
    objective: str
    domain: str
    questions: List[ResearchQuestion] = field(default_factory=list)
    hypotheses: List[HypothesisRecord] = field(default_factory=list)
    experiments: List[ExperimentRecord] = field(default_factory=list)
    discoveries: List[str] = field(default_factory=list)  # packet ids
    failed_approaches: List[str] = field(default_factory=list)
    participants: Set[str] = field(default_factory=set)
    status: str = "active"


class ResearchAgenda:
    """Self-expanding frontier: what don't we know?"""

    def __init__(self):
        self.questions: List[ResearchQuestion] = []

    def add(self, text: str, domain: str, priority: float = 0.5, source: str = "frontier") -> ResearchQuestion:
        q = ResearchQuestion(new_id(), text, domain, priority, source)
        self.questions.append(q)
        return q

    def from_gaps(self, gaps: List[str], domain: str = "general") -> List[ResearchQuestion]:
        out = []
        for g in gaps:
            out.append(self.add(f"What explains {g}?", domain, priority=0.7, source="gap"))
        return out

    def from_contradiction(self, description: str, domain: str) -> ResearchQuestion:
        return self.add(description, domain, priority=0.9, source="contradiction")

    def top(self, n: int = 5) -> List[ResearchQuestion]:
        return sorted(self.questions, key=lambda q: -q.priority)[:n]


class KnowledgeGraph:
    """Scientific memory: nodes + typed edges."""

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Tuple[str, str, str]] = []  # (from, rel, to)

    def add_node(self, node_id: str, kind: str, data: Optional[Dict] = None) -> None:
        self.nodes[node_id] = {"kind": kind, **(data or {})}

    def link(self, a: str, rel: str, b: str) -> None:
        self.edges.append((a, rel, b))

    def supports(self, discovery_id: str, hypothesis_id: str) -> None:
        self.link(discovery_id, "supports", hypothesis_id)

    def contradicts(self, discovery_id: str, hypothesis_id: str) -> None:
        self.link(discovery_id, "contradicts", hypothesis_id)

    def neighbors(self, node_id: str) -> List[Tuple[str, str]]:
        return [(rel, b) for a, rel, b in self.edges if a == node_id]


class ScienceLayer:
    """Civilization science institution under CCOS (caller enforces capabilities)."""

    def __init__(self):
        self.programs: Dict[str, ResearchProgram] = {}
        self.agenda = ResearchAgenda()
        self.graph = KnowledgeGraph()
        self.archive_experiments: List[ExperimentRecord] = []
        self.failed_hypotheses: List[HypothesisRecord] = []
        self.teaching = TeachingProtocol()
        self.collab = CollaborationCoordinator()
        self.verified_civilization: Dict[str, KnowledgePacket] = {}  # only after verification

    def open_program(self, objective: str, domain: str, agent_id: str) -> ResearchProgram:
        prog = ResearchProgram(new_id(), objective, domain, participants={agent_id})
        self.programs[prog.program_id] = prog
        q = self.agenda.add(f"Program: {objective}", domain, 0.8, "frontier")
        prog.questions.append(q)
        self.graph.add_node(prog.program_id, "program", {"objective": objective, "domain": domain})
        return prog

    def propose_hypothesis(
        self, program_id: str, question_id: str, statement: str, author_id: str
    ) -> Optional[HypothesisRecord]:
        prog = self.programs.get(program_id)
        if not prog:
            return None
        h = HypothesisRecord(new_id(), question_id, statement, author_id)
        prog.hypotheses.append(h)
        prog.participants.add(author_id)
        self.graph.add_node(h.hypothesis_id, "hypothesis", {"statement": statement})
        self.graph.link(h.hypothesis_id, "addresses", question_id)
        return h

    def record_experiment(
        self,
        program_id: str,
        hypothesis_id: str,
        researcher_id: str,
        inputs: Dict[str, Any],
        procedure: str,
        output: Dict[str, Any],
        result: str,
        evidence_hash: str,
        environment: str = "sandbox",
        capabilities: Optional[List[str]] = None,
    ) -> ExperimentRecord:
        exp = ExperimentRecord(
            new_id(), hypothesis_id, researcher_id, environment, inputs, procedure,
            capabilities or [], output, evidence_hash, result,
        )
        prog = self.programs.get(program_id)
        if prog:
            prog.experiments.append(exp)
            prog.participants.add(researcher_id)
        self.archive_experiments.append(exp)
        self.graph.add_node(exp.experiment_id, "experiment", {"result": result})
        self.graph.link(exp.experiment_id, "tests", hypothesis_id)
        return exp

    def falsify_hypothesis(self, program_id: str, hypothesis_id: str, reason: str) -> bool:
        prog = self.programs.get(program_id)
        if not prog:
            return False
        for h in prog.hypotheses:
            if h.hypothesis_id == hypothesis_id:
                h.status = "falsified"
                prog.failed_approaches.append(f"{hypothesis_id}:{reason}")
                self.failed_hypotheses.append(h)
                return True
        return False

    def promote_discovery(
        self, program_id: str, packet: KnowledgePacket, verifier_ids: List[str]
    ) -> bool:
        """Only after independent verification — never from single teacher."""
        if not verifier_ids:
            return False
        prog = self.programs.get(program_id)
        if not prog:
            return False
        self.verified_civilization[packet.packet_id] = packet
        prog.discoveries.append(packet.packet_id)
        self.graph.add_node(packet.packet_id, "discovery", {"claim": packet.claim})
        self.graph.link(packet.packet_id, "discovered_by", packet.creator_id)
        return True

    def replicate_experiment(self, experiment_id: str, researcher_id: str) -> Optional[ExperimentRecord]:
        src = next((e for e in self.archive_experiments if e.experiment_id == experiment_id), None)
        if not src or not src.reproducible:
            return None
        # Independent run: same inputs/procedure, new id
        clone = ExperimentRecord(
            new_id(), src.hypothesis_id, researcher_id, src.environment,
            dict(src.inputs), src.procedure, list(src.capability_requirements),
            dict(src.output), src.evidence_hash, src.result, True,
        )
        self.archive_experiments.append(clone)
        self.graph.link(clone.experiment_id, "replicates", src.experiment_id)
        return clone

    def summary(self) -> Dict[str, Any]:
        return {
            "programs": len(self.programs),
            "agenda_questions": len(self.agenda.questions),
            "experiments_archived": len(self.archive_experiments),
            "failed_hypotheses": len(self.failed_hypotheses),
            "civilization_discoveries": len(self.verified_civilization),
            "graph_nodes": len(self.graph.nodes),
            "graph_edges": len(self.graph.edges),
        }
