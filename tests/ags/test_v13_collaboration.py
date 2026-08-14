"""v1.3 Collaborative intelligence tests."""

from ags.collaboration.team import (
    CollaborationCoordinator, ResearchProblem, Role,
)
from ags.v12.teaching import SocialEpistemicMemory, BeliefState


def test_team_formation_and_roles():
    coord = CollaborationCoordinator()
    problem = ResearchProblem("p1", "Explain output", "math")
    team = coord.create_team(problem)
    assert coord.volunteer(team.team_id, "a", Role.THEORIST)
    assert coord.volunteer(team.team_id, "b", Role.EXPERIMENTER)
    assert coord.volunteer(team.team_id, "c", Role.VERIFIER)
    assert team.status == "active"
    # duplicate role rejected
    assert not coord.volunteer(team.team_id, "d", Role.THEORIST)


def test_hypothesis_and_evidence_roles():
    coord = CollaborationCoordinator()
    problem = ResearchProblem("p2", "model output", "math")
    team = coord.create_team(problem)
    coord.volunteer(team.team_id, "theorist", Role.THEORIST)
    coord.volunteer(team.team_id, "exp", Role.EXPERIMENTER)
    h = coord.submit_hypothesis(team.team_id, "theorist", "output=x+y+z", {"form": "linear"})
    assert h is not None
    # experimenter cannot submit hypothesis
    assert coord.submit_hypothesis(team.team_id, "exp", "bad", {}) is None
    e = coord.submit_evidence(team.team_id, "exp", [{"x": 1, "y": 1, "z": 1, "output": 3}])
    assert e is not None
    assert len(team.evidence_pool) == 1


def test_collective_claim_verification():
    coord = CollaborationCoordinator()
    problem = ResearchProblem("p3", "discover sum", "math")
    team = coord.create_team(problem)
    coord.volunteer(team.team_id, "a", Role.THEORIST)
    coord.volunteer(team.team_id, "b", Role.EXPERIMENTER)
    coord.volunteer(team.team_id, "c", Role.VERIFIER)
    evidence = [
        {"x": 1.0, "y": 1.0, "z": 1.0, "output": 3.0},
        {"x": 2.0, "y": 1.0, "z": 1.0, "output": 4.0},
        {"x": 1.0, "y": 2.0, "z": 1.0, "output": 4.0},
        {"x": 1.0, "y": 1.0, "z": 2.0, "output": 4.0},
    ]
    coord.submit_evidence(team.team_id, "b", evidence)
    packet = coord.publish_team_claim(
        team.team_id, "a", "output = x+y+z", "output",
        {"coeffs": [1, 1, 1], "intercept": 0, "rmse": 0.001, "inputs": ["x", "y", "z"]},
        evidence,
    )
    assert packet is not None
    mem = SocialEpistemicMemory("c")
    state = coord.peer_verify(team.team_id, "c", packet, mem)
    assert state == BeliefState.VERIFIED
    assert team.problem.status == "solved"
    m = coord.metrics(team.team_id)
    assert m["solved"] is True
