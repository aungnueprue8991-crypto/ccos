"""AGS v1.3 — Collaborative Intelligence (teams, roles, evidence pool)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ags.shared.types import new_id, now_ts
from ags.v12.teaching import KnowledgePacket, TeachingProtocol, SocialEpistemicMemory, BeliefState


class Role(str, Enum):
    THEORIST = "theorist"
    EXPERIMENTER = "experimenter"
    VERIFIER = "verifier"
    COORDINATOR = "coordinator"


@dataclass
class ResearchProblem:
    problem_id: str
    statement: str
    domain: str
    required_roles: List[Role] = field(default_factory=lambda: [Role.THEORIST, Role.EXPERIMENTER, Role.VERIFIER])
    status: str = "open"  # open | active | solved | failed


@dataclass
class Contribution:
    contribution_id: str
    agent_id: str
    role: Role
    kind: str  # hypothesis | evidence | challenge | verification
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=now_ts)


@dataclass
class ResearchTeam:
    team_id: str
    problem: ResearchProblem
    members: Dict[str, Role] = field(default_factory=dict)
    contributions: List[Contribution] = field(default_factory=list)
    evidence_pool: List[Dict[str, Any]] = field(default_factory=list)
    claims: List[KnowledgePacket] = field(default_factory=list)
    status: str = "forming"  # forming | active | reviewing | complete
    result: Optional[Dict[str, Any]] = None

    def assign(self, agent_id: str, role: Role) -> None:
        self.members[agent_id] = role

    def add_contribution(self, agent_id: str, role: Role, kind: str, payload: Dict[str, Any]) -> Contribution:
        c = Contribution(new_id(), agent_id, role, kind, payload)
        self.contributions.append(c)
        if kind == "evidence" and "samples" in payload:
            self.evidence_pool.extend(payload["samples"])
        return c


class CollaborationCoordinator:
    """Forms teams, tracks contributions, requires verification — not majority vote."""

    def __init__(self):
        self.teams: Dict[str, ResearchTeam] = {}
        self.teaching = TeachingProtocol()

    def create_team(self, problem: ResearchProblem) -> ResearchTeam:
        team = ResearchTeam(team_id=new_id(), problem=problem, status="forming")
        self.teams[team.team_id] = team
        problem.status = "active"
        return team

    def volunteer(self, team_id: str, agent_id: str, role: Role) -> bool:
        team = self.teams.get(team_id)
        if not team or role in team.members.values():
            # allow only one per role for simplicity in v1.3
            if team and role in team.members.values():
                return False
        if not team:
            return False
        team.assign(agent_id, role)
        if len(team.members) >= len(team.problem.required_roles):
            team.status = "active"
        return True

    def submit_hypothesis(self, team_id: str, agent_id: str, statement: str, model: Dict) -> Optional[Contribution]:
        team = self.teams.get(team_id)
        if not team or team.members.get(agent_id) not in (Role.THEORIST, Role.COORDINATOR):
            return None
        return team.add_contribution(agent_id, team.members[agent_id], "hypothesis", {
            "statement": statement, "model": model,
        })

    def submit_evidence(self, team_id: str, agent_id: str, samples: List[Dict]) -> Optional[Contribution]:
        team = self.teams.get(team_id)
        if not team or team.members.get(agent_id) not in (Role.EXPERIMENTER, Role.COORDINATOR):
            return None
        return team.add_contribution(agent_id, team.members[agent_id], "evidence", {"samples": samples})

    def publish_team_claim(
        self, team_id: str, publisher_id: str, claim: str, target: str, model: Dict, evidence: List[Dict]
    ) -> Optional[KnowledgePacket]:
        team = self.teams.get(team_id)
        if not team:
            return None
        packet = self.teaching.teach(publisher_id, claim, target, model, evidence, confidence=0.85)
        team.claims.append(packet)
        team.status = "reviewing"
        return packet

    def peer_verify(
        self, team_id: str, verifier_id: str, packet: KnowledgePacket, student_mem: SocialEpistemicMemory
    ) -> BeliefState:
        team = self.teams.get(team_id)
        if not team or team.members.get(verifier_id) != Role.VERIFIER:
            return BeliefState.REJECTED
        state = self.teaching.receive_and_evaluate(student_mem, packet)
        team.add_contribution(verifier_id, Role.VERIFIER, "verification", {
            "packet_id": packet.packet_id, "state": state.value,
        })
        if state == BeliefState.VERIFIED:
            team.status = "complete"
            team.problem.status = "solved"
            team.result = {"packet_id": packet.packet_id, "verified_by": verifier_id}
        return state

    def metrics(self, team_id: str) -> Dict[str, Any]:
        team = self.teams.get(team_id)
        if not team:
            return {}
        return {
            "members": len(team.members),
            "contributions": len(team.contributions),
            "evidence_samples": len(team.evidence_pool),
            "claims": len(team.claims),
            "status": team.status,
            "solved": team.problem.status == "solved",
        }
